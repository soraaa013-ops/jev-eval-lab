# JudgeBench qualitative error audit

High-confidence errors are ranked by the probability assigned to the selected answer.

## jev

Errors: 153/700. Top 15 high-confidence failures:

| item | orientation | source | gold | choice | confidence |
|---|---|---|---:|---:|---:|
| 49c0f568-1ac2-53dc-be78-f3eea93820fd | original | mmlu-pro-biology | A | B | 0.990 |
| df6e9ec0-0bd1-51ec-a81f-3a58cc415253 | original | mmlu-pro-biology | B | A | 0.960 |
| 49c0f568-1ac2-53dc-be78-f3eea93820fd | swapped | mmlu-pro-biology | B | A | 0.940 |
| cc8d0d03-7d7e-5728-8bd6-fa03589c976d | original | mmlu-pro-psychology | B | A | 0.920 |
| a1b1ff8a-eae1-5c68-b5b1-4d50cb2afc17 | original | mmlu-pro-health | A | B | 0.910 |
| b958ea91-8f2a-55be-8c8b-d61cf90f5076 | original | mmlu-pro-philosophy | A | B | 0.900 |
| df6e9ec0-0bd1-51ec-a81f-3a58cc415253 | swapped | mmlu-pro-biology | A | B | 0.880 |
| 83adf077-567f-5ce2-91e7-bf02decdaa21 | original | mmlu-pro-engineering | B | A | 0.870 |
| 35eb196e-50d4-5501-8f44-cc5dc85f6291 | original | mmlu-pro-chemistry | B | A | 0.850 |
| 1c76021c-cb8e-5477-8f7e-88855d6dd547 | original | mmlu-pro-health | A | B | 0.830 |
| 37577e35-cf0b-5880-97a1-857736d76651 | swapped | mmlu-pro-health | B | A | 0.830 |
| 37577e35-cf0b-5880-97a1-857736d76651 | original | mmlu-pro-health | A | B | 0.820 |
| cc8d0d03-7d7e-5728-8bd6-fa03589c976d | swapped | mmlu-pro-psychology | A | B | 0.820 |
| cdc80d94-4fc3-5b62-88fc-167006f3b7bd | original | livebench-reasoning | B | A | 0.820 |
| 0ffbf15d-cbdf-5569-928b-adf90e0df935 | original | livebench-math | A | B | 0.810 |

## gpt5mini

Errors: 100/700. Top 15 high-confidence failures:

| item | orientation | source | gold | choice | confidence |
|---|---|---|---:|---:|---:|
| e49c100d-761c-5b04-8145-e94fbc847864 | swapped | livebench-reasoning | B | A | 1.000 |
| 49c0f568-1ac2-53dc-be78-f3eea93820fd | original | mmlu-pro-biology | A | B | 0.980 |
| df6e9ec0-0bd1-51ec-a81f-3a58cc415253 | swapped | mmlu-pro-biology | A | B | 0.980 |
| a6f94de7-dee6-579b-852a-1be7ca389cd2 | swapped | mmlu-pro-physics | A | B | 0.980 |
| 8b33bb85-b242-5845-83f0-5cb7e32be529 | swapped | mmlu-pro-business | A | B | 0.980 |
| 943bf94c-9ba1-5b9b-9ec4-038c8f3e11d7 | swapped | livebench-math | A | B | 0.980 |
| 6dcc9ad7-2f3b-5dae-be24-9080b9ad7973 | original | livebench-reasoning | A | B | 0.980 |
| 7a2a5167-8e15-50ff-b984-335d814cc77d | swapped | livebench-reasoning | A | B | 0.980 |
| 943bf94c-9ba1-5b9b-9ec4-038c8f3e11d7 | original | livebench-math | B | A | 0.970 |
| a4eff39a-4f2e-5cee-a6de-b8e74625269f | swapped | mmlu-pro-law | B | A | 0.950 |
| a4eff39a-4f2e-5cee-a6de-b8e74625269f | original | mmlu-pro-law | A | B | 0.950 |
| e302b0a0-28d5-5a3c-b1af-fedcf5543e72 | swapped | mmlu-pro-law | B | A | 0.950 |
| 2328c85f-6803-5f2c-9ccb-f429dea4428c | swapped | mmlu-pro-biology | A | B | 0.950 |
| df6e9ec0-0bd1-51ec-a81f-3a58cc415253 | original | mmlu-pro-biology | B | A | 0.950 |
| 49c0f568-1ac2-53dc-be78-f3eea93820fd | swapped | mmlu-pro-biology | B | A | 0.950 |

## qwen

Errors: 250/700. Top 15 high-confidence failures:

| item | orientation | source | gold | choice | confidence |
|---|---|---|---:|---:|---:|
| c7aaeea9-830b-56fc-b12c-23ca19c3bb29 | swapped | mmlu-pro-biology | A | B | 1.000 |
| 49c0f568-1ac2-53dc-be78-f3eea93820fd | original | mmlu-pro-biology | A | B | 1.000 |
| 79d55355-34c0-5ba7-842e-65671b9858d9 | swapped | mmlu-pro-biology | A | B | 1.000 |
| 799a7559-a3b1-5dc3-bec3-54d5e930fd24 | original | mmlu-pro-computer science | A | B | 1.000 |
| 544ae546-5220-5ffd-86f3-5b44d4422ab7 | original | mmlu-pro-computer science | A | B | 1.000 |
| 9e079604-2288-52ba-9d89-4868ccd34200 | original | mmlu-pro-computer science | A | B | 1.000 |
| 9eea6f37-5da7-5b9e-81f7-6f27eccf11da | original | mmlu-pro-health | A | B | 1.000 |
| 0f999ea7-10a1-5b85-a175-b86d50338266 | original | mmlu-pro-history | A | B | 1.000 |
| 9536d58f-8a88-53be-b97e-45bb2d457c12 | original | mmlu-pro-psychology | A | B | 1.000 |
| a13f48e6-1d51-5076-94bf-ff0303e4c198 | original | mmlu-pro-other | A | B | 1.000 |
| 70bf4c34-6b15-53e6-bb19-9094bdaf6c9f | swapped | mmlu-pro-philosophy | A | B | 1.000 |
| 2f665bcd-7aee-539b-9acf-142548185b64 | swapped | mmlu-pro-philosophy | B | A | 1.000 |
| 766bdf22-3677-53bf-9c46-4fb984430682 | swapped | mmlu-pro-economics | A | B | 1.000 |
| 12ab4b20-e60b-59ca-b20b-500b12900def | swapped | mmlu-pro-economics | A | B | 1.000 |
| 40c35c1b-4d3a-56ae-a7fa-22307efca211 | original | mmlu-pro-math | A | B | 1.000 |

## skywork

Errors: 278/700. Top 15 high-confidence failures:

| item | orientation | source | gold | choice | confidence |
|---|---|---|---:|---:|---:|
| be6b6818-ae30-57de-9c58-418073c98259 | original | livebench-reasoning | A | B | 0.998 |
| be6b6818-ae30-57de-9c58-418073c98259 | swapped | livebench-reasoning | B | A | 0.998 |
| dcfbadd5-4b7c-5ffd-b66d-5cb0a380605d | original | mmlu-pro-philosophy | A | B | 0.997 |
| dcfbadd5-4b7c-5ffd-b66d-5cb0a380605d | swapped | mmlu-pro-philosophy | B | A | 0.997 |
| 04a6b0ff-7e1d-5f39-b615-7e379aa1864a | original | livecodebench | B | A | 0.995 |
| 04a6b0ff-7e1d-5f39-b615-7e379aa1864a | swapped | livecodebench | A | B | 0.995 |
| d71a5264-231b-5af8-829d-9ee50f0acf90 | original | livebench-math | A | B | 0.992 |
| d71a5264-231b-5af8-829d-9ee50f0acf90 | swapped | livebench-math | B | A | 0.992 |
| 2d989dfb-7cf0-549e-945c-3dd060d1fad5 | original | mmlu-pro-law | A | B | 0.991 |
| 2d989dfb-7cf0-549e-945c-3dd060d1fad5 | swapped | mmlu-pro-law | B | A | 0.991 |
| 2862a52e-5004-549c-8cd9-d499f752d0e1 | original | livebench-math | A | B | 0.990 |
| 2862a52e-5004-549c-8cd9-d499f752d0e1 | swapped | livebench-math | B | A | 0.990 |
| 803e5d58-0c62-5946-9738-ceeea2e4aaa2 | original | mmlu-pro-psychology | B | A | 0.987 |
| 803e5d58-0c62-5946-9738-ceeea2e4aaa2 | swapped | mmlu-pro-psychology | A | B | 0.987 |
| ef607538-1628-5cce-bc92-093ff755586d | original | mmlu-pro-psychology | B | A | 0.987 |
