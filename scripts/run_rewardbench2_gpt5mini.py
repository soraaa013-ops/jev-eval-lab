"""Run GPT-5 mini on the same RB2 winner-selection tasks as GPT-5."""
import sys
import run_rewardbench2_gpt5 as runner

if __name__ == '__main__':
    runner.MODEL = 'openai/gpt-5-mini'
    runner.OUT = runner.ROOT / 'artifacts/rewardbench2-gpt5mini'
    runner.VERSION = 'rb2-gpt5-mini-medium-ranking-v1'
    if any(a == '--mode' or a.startswith('--mode=') for a in sys.argv):
        raise SystemExit('This runner is ranking-only; omit --mode.')
    sys.argv += ['--mode', 'ranking']
    runner.main()
