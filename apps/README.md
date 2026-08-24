# Application Entry Points

Active study applications:

- `study1_validation.py`: shared six-profile expert-validation application;
- `study2_01_lowP_lowA_noF.py`: `P0_A0_F0`;
- `study2_02_lowP_lowA_F.py`: `P0_A0_F1`;
- `study2_03_lowP_highA_noF.py`: `P0_A1_F0`;
- `study2_04_lowP_highA_F.py`: `P0_A1_F1`;
- `study2_05_highP_lowA_noF.py`: `P1_A0_F0`;
- `study2_06_highP_lowA_F.py`: `P1_A0_F1`;
- `study2_07_highP_highA_noF.py`: `P1_A1_F0`;
- `study2_08_highP_highA_F.py`: `P1_A1_F1`.

Each Study 2 entry point calls the shared `xai_as_closure.study2_app` with one
hard-coded condition. If Qualtrics supplies `cond`, it must match that condition;
the app rejects a mismatch.
