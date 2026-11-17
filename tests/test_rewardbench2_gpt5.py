import json
import sys
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import requests, numpy
except ImportError:
    raise unittest.SkipTest('Install .[agent-eval] for GPT-5 RewardBench 2 tests')
from run_rewardbench2_gpt5 import payload, parse, load_rows, read_records, canonical, combine_events, rejected_for_budget
from analyze_rewardbench2_gpt5 import rating_verdict, identity, ties_score

class GPT5RB2Tests(unittest.TestCase):
    def setUp(self):
        self.row={'id':'test','prompt':'task','chosen':['good'], 'rejected':['bad1','bad2','bad3'], 'secret_gold':'DO_NOT_SEND','subset':'Math'}
    def response(self,value):
        return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(value)}}]}
    def test_blind_and_rotation(self):
        for mode in ['ranking','rating']:
            p=payload(self.row,mode)
            self.assertNotIn('DO_NOT_SEND',str(p))
            state=json.loads(p['messages'][1]['content'])
            self.assertNotIn('chosen',state)
            if mode=='ranking':
                label=next(k for k,v in state['candidates'].items() if v=='good')
                self.assertTrue(parse(self.response({'choice':label}),self.row,mode)['correct'])
    def test_mini_changes_only_model_in_matched_ranking_request(self):
        full=payload(self.row,'ranking')
        with patch('run_rewardbench2_gpt5.MODEL','openai/gpt-5-mini'):
            mini=payload(self.row,'ranking')
        self.assertEqual(mini,{**full,'model':'openai/gpt-5-mini'})
    def test_rating_mapping_and_invalid_outputs(self):
        values={'scores':{'c0':3.5,'c1':2,'c2':1,'c3':0}}
        self.assertEqual(parse(self.response(values),self.row,'rating')['scores'],[3.5,2,1,0])
        for value in [True, float('nan'),5]:
            values['scores']['c0']=value
            with self.assertRaises(ValueError):parse(self.response(values),self.row,'rating')
        with self.assertRaises(ValueError):parse(self.response({'scores':{'c0':2}}),self.row,'rating')
    def test_jsonl_unicode_separator_is_content_not_a_record(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'records.jsonl'
            row={'text':'first\u2028second\u0085third'}
            p.write_text(canonical(row)+'\n'+canonical({'text':'next'})+'\n')
            self.assertEqual(read_records(p),[row,{'text':'next'}])
    def test_ids_are_unique_only_with_subset(self):
        rows=load_rows()
        self.assertEqual(len(rows),1865)
        self.assertLess(len({str(r['id']) for r in rows}),len(rows))
        self.assertEqual(len({identity(r) for r in rows}),len(rows))
    def test_rating_ties_and_missing_are_not_silently_dropped(self):
        v=rating_verdict(self.row,{'scores':[2.8,2.8,1,0]})
        self.assertTrue(v['top1'])
        self.assertFalse(v['strict'])
        self.assertEqual(v['correct_pairs'],2)
        missing=rating_verdict(self.row,{'success':False})
        self.assertFalse(missing['top1'])
        self.assertFalse(missing['strict'])
        self.assertEqual(missing['correct_pairs'],0)
        self.assertEqual(missing['total_pairs'],3)
    def test_only_unbilled_admission_rejections_can_be_recovered(self):
        blocked={'subset':'Math','id':'x','mode':'ranking','request_sha256':'same','success':False,'attempts':[{'status':402,'response':{'error':{}}}],'reported_cost_all_attempts':0}
        success={**blocked,'success':True,'recovery':True,'attempts':[{'status':200,'response':{'usage':{'cost':.1}}}],'reported_cost_all_attempts':.1}
        combined=combine_events([blocked,success])['Math','x','ranking']
        self.assertTrue(combined['success'])
        self.assertEqual(len(combined['attempts']),2)
        self.assertEqual(combined['reported_cost_all_attempts'],.1)
        with self.assertRaises(AssertionError):combine_events([success,success])
        billed={**blocked,'attempts':[{'status':402,'response':{'usage':{'cost':.1}}}]}
        self.assertFalse(rejected_for_budget(billed))
    def test_truncated_generation_rejected(self):
        body=self.response({'choice':'A'});body['choices'][0]['finish_reason']='length'
        with self.assertRaises(ValueError):parse(body,self.row,'ranking')

if __name__=='__main__':unittest.main()
