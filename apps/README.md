# Application Entry Points

Active study applications:

- `study1_validation.py`: earlier expert-validation entry point;
- `study1_validation_v2.py`: standalone second expert assessment, using the shared v6 materials and separate round-2 records. See `study_CHI/STUDY1_ROUND2_LAUNCH.md`;
- `study2_01_lowP_lowA_noF.py`: `P0_A0_F0`;
- `study2_02_lowP_lowA_F.py`: `P0_A0_F1`;
- `study2_03_lowP_highA_noF.py`: `P0_A1_F0`;
- `study2_04_lowP_highA_F.py`: `P0_A1_F1`;
- `study2_05_highP_lowA_noF.py`: `P1_A0_F0`;
- `study2_06_highP_lowA_F.py`: `P1_A0_F1`;
- `study2_07_highP_highA_noF.py`: `P1_A1_F0`;
- `study2_08_highP_highA_F.py`: `P1_A1_F1`.

The filenames and `P0`/`P1` condition IDs are retained as stable deployment
keys for existing Streamlit and Qualtrics routes. In the active design, `P0`
means **explanation absent** and `P1` means **explanation present**; they are not
low/high levels of explainability.

Each Study 2 entry point calls the shared `xai_as_closure.study2_app` with one
hard-coded condition. If Qualtrics supplies `cond`, it must match that condition;
the app rejects a mismatch.

## Local researcher review

`local_review.py` is a local-only review hub, not a participant entry point. Start all eight task previews with `python tools/local_study2.py`, then start the hub with `STUDY2_LOCAL_PREVIEW=1 python -m streamlit run apps/local_review.py --server.address 127.0.0.1 --server.port 8500`. See study_CHI/STUDY2_LOCAL_PREPARATION.md. Preview sessions are synthetic, isolated and never remotely saved.
