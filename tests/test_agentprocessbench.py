import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import numpy,requests
except ImportError:
    raise unittest.SkipTest('Install .[agent-eval] for trajectory-judge tests')
from run_agentprocessbench import evidence,payload,parse,MODELS
from analyze_agentprocessbench import scores
class AgentJudgeTests(unittest.TestCase):
    def setUp(self):
        self.r={'question':'task','messages':[{'role':'user','content':'request'},{'role':'assistant','content':'action'}],'ground_truth':'SECRET_GOLD','answer_text':'SECRET_ANSWER','tool_metrics':{'SECRET_METRIC':True},'step_labels':{'1':-1},'final_label':-1}
    def test_gold_and_metrics_never_enter_requests(self):
        for model in MODELS:
            p=str(payload(self.r,model));self.assertNotIn('SECRET_',p)
        self.assertEqual(evidence(self.r)['assistant_message_indices'],[1])
    def test_missing_steps_rejected(self):
        with self.assertRaises(AssertionError):parse({'choices':[{'message':{'content':'{"step_labels":{},"final_label":1}'}}]},'gpt5mini',self.r)
    def test_decision_labels_mapped_semantically(self):
        p=parse({'answers':{'step_1':{'choice':'negative'},'final':{'choice':'positive'}}},'jev',self.r)
        self.assertEqual(p,{'step_labels':{'1':-1},'final_label':1})
    def test_missing_predictions_count_as_wrong(self):
        s=scores([[1,0,0,1],[0,1,0,0],[0,0,1,0]])
        self.assertEqual(s['n_steps'],4);self.assertEqual(s['accuracy'],.75);self.assertEqual(s['error_recall'],.5)
if __name__=='__main__':unittest.main()
