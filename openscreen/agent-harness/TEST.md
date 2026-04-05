# Openscreen CLI — Test Results

## Summary

- **Total tests**: 50
- **Passed**: 50
- **Failed**: 0
- **Test suites**: 2 (unit + end-to-end)

## Test Suites

### test_core.py — Unit Tests (37 tests, no ffmpeg required)

| # | Test | Status |
|---|------|--------|
| 1 | TestSession::test_new_session | PASSED |
| 2 | TestSession::test_new_session_with_id | PASSED |
| 3 | TestSession::test_new_project | PASSED |
| 4 | TestSession::test_new_project_with_video | PASSED |
| 5 | TestSession::test_undo_redo | PASSED |
| 6 | TestSession::test_undo_clears_redo | PASSED |
| 7 | TestSession::test_save_load_project | PASSED |
| 8 | TestSession::test_open_nonexistent | PASSED |
| 9 | TestSession::test_save_without_path | PASSED |
| 10 | TestSession::test_status | PASSED |
| 11 | TestProject::test_new_project | PASSED |
| 12 | TestProject::test_info | PASSED |
| 13 | TestProject::test_info_without_project | PASSED |
| 14 | TestProject::test_set_setting | PASSED |
| 15 | TestProject::test_set_invalid_setting | PASSED |
| 16 | TestZoom::test_add_zoom | PASSED |
| 17 | TestZoom::test_list_zoom | PASSED |
| 18 | TestZoom::test_remove_zoom | PASSED |
| 19 | TestZoom::test_remove_nonexistent_zoom | PASSED |
| 20 | TestZoom::test_invalid_depth | PASSED |
| 21 | TestZoom::test_invalid_focus | PASSED |
| 22 | TestZoom::test_invalid_time_range | PASSED |
| 23 | TestZoom::test_zoom_undo | PASSED |
| 24 | TestSpeed::test_add_speed | PASSED |
| 25 | TestSpeed::test_invalid_speed | PASSED |
| 26 | TestSpeed::test_list_and_remove | PASSED |
| 27 | TestTrim::test_add_trim | PASSED |
| 28 | TestTrim::test_list_and_remove | PASSED |
| 29 | TestCrop::test_default_crop | PASSED |
| 30 | TestCrop::test_set_crop | PASSED |
| 31 | TestCrop::test_invalid_crop | PASSED |
| 32 | TestCrop::test_crop_out_of_bounds | PASSED |
| 33 | TestAnnotation::test_add_text_annotation | PASSED |
| 34 | TestAnnotation::test_list_and_remove | PASSED |
| 35 | TestIntegration::test_full_workflow | PASSED |
| 36 | TestIntegration::test_export_presets | PASSED |

### test_full_e2e.py — End-to-End Tests (14 tests, requires ffmpeg)

| # | Test | Status |
|---|------|--------|
| 37 | TestMediaE2E::test_probe_real_video | PASSED |
| 38 | TestMediaE2E::test_check_video | PASSED |
| 39 | TestMediaE2E::test_check_invalid_video | PASSED |
| 40 | TestMediaE2E::test_extract_thumbnail | PASSED |
| 41 | TestMediaE2E::test_extract_frames | PASSED |
| 42 | TestExportE2E::test_basic_export | PASSED |
| 43 | TestExportE2E::test_export_with_zoom | PASSED |
| 44 | TestExportE2E::test_export_with_speed | PASSED |
| 45 | TestExportE2E::test_export_with_trim | PASSED |
| 46 | TestExportE2E::test_export_complex | PASSED |
| 47 | TestCLISubprocess::test_cli_help | PASSED |
| 48 | TestCLISubprocess::test_cli_version | PASSED |
| 49 | TestCLISubprocess::test_cli_export_presets | PASSED |
| 50 | TestCLISubprocess::test_cli_media_probe | PASSED |

## Raw pytest output

```
============================= test session starts ==============================
platform linux -- Python 3.11.2, pytest-9.0.2, pluggy-1.6.0
collected 50 items

cli_anything/openscreen/tests/test_core.py ....................................  [ 72%]
cli_anything/openscreen/tests/test_full_e2e.py ..............                    [100%]

============================= 50 passed in 29.35s ==============================
```

## Environment

- Python: 3.11.2
- pytest: 9.0.2
- ffmpeg: 5.1.6
- OS: Linux (Debian)
