"""End-to-end tests for Openscreen CLI — requires ffmpeg installed.

These tests create real video files, run the full export pipeline,
and verify outputs with ffprobe.
"""

import json
import os
import subprocess
import tempfile

import pytest

from cli_anything.openscreen.core.session import Session
from cli_anything.openscreen.core import project as proj_mod
from cli_anything.openscreen.core import timeline as tl_mod
from cli_anything.openscreen.core import export as export_mod
from cli_anything.openscreen.core import media as media_mod
from cli_anything.openscreen.utils import ffmpeg_backend


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def test_video():
    """Create a 5-second test video with ffmpeg."""
    tmpdir = tempfile.mkdtemp()
    video_path = os.path.join(tmpdir, "test_recording.mp4")

    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i",
            "testsrc=duration=5:size=1920x1080:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            video_path,
        ], capture_output=True, check=True, timeout=30)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("ffmpeg not available")

    yield video_path

    # Cleanup
    try:
        os.remove(video_path)
        os.rmdir(tmpdir)
    except OSError:
        pass


@pytest.fixture
def session(test_video):
    """Create a session with a project and test video attached."""
    s = Session()
    s.new_project(test_video)
    return s


# ── Media Tests ───────────────────────────────────────────────────────────

class TestMediaE2E:
    def test_probe_real_video(self, test_video):
        result = media_mod.probe(test_video)
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["duration"] > 4.0
        assert result["codec"] == "h264"
        assert result["has_audio"] is True

    def test_check_video(self, test_video):
        result = media_mod.check_video(test_video)
        assert result["valid"] is True
        assert result["width"] == 1920

    def test_check_invalid_video(self):
        result = media_mod.check_video("/nonexistent/file.mp4")
        assert result["valid"] is False

    def test_extract_thumbnail(self, test_video):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            thumb_path = f.name
        try:
            result = media_mod.extract_thumbnail(test_video, thumb_path, time_s=1.0)
            assert os.path.exists(thumb_path)
            assert result["file_size"] > 0
        finally:
            os.unlink(thumb_path)

    def test_extract_frames(self, test_video):
        tmpdir = tempfile.mkdtemp()
        try:
            frames = ffmpeg_backend.extract_frames(test_video, tmpdir, fps=2, max_frames=10)
            assert len(frames) > 0
            assert all(f.endswith(".jpg") for f in frames)
            assert all(os.path.getsize(f) > 0 for f in frames)
        finally:
            import shutil
            shutil.rmtree(tmpdir)


# ── Export Tests ──────────────────────────────────────────────────────────

class TestExportE2E:
    def test_basic_export(self, session):
        """Export with default settings (no regions)."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            out_path = f.name
        try:
            result = export_mod.render(session, out_path)
            assert os.path.exists(out_path)
            assert result["file_size"] > 0
            assert result["width"] > 0
            assert result["codec"] == "h264"
            assert result["segments_rendered"] >= 1
        finally:
            os.unlink(out_path)

    def test_export_with_zoom(self, session):
        """Export with a zoom region."""
        tl_mod.add_zoom_region(session, 1000, 3000, depth=3, focus_x=0.7, focus_y=0.3)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            out_path = f.name
        try:
            result = export_mod.render(session, out_path)
            assert os.path.exists(out_path)
            assert result["file_size"] > 0
            assert result["segments_rendered"] >= 2  # before, during, after zoom
        finally:
            os.unlink(out_path)

    def test_export_with_speed(self, session):
        """Export with a speed region."""
        tl_mod.add_speed_region(session, 2000, 4000, speed=2.0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            out_path = f.name
        try:
            result = export_mod.render(session, out_path)
            assert os.path.exists(out_path)
            assert result["file_size"] > 0
            # Output should be shorter than source due to 2x speed section
            assert result["duration"] < 5.0
        finally:
            os.unlink(out_path)

    def test_export_with_trim(self, session):
        """Export with a trim region."""
        tl_mod.add_trim_region(session, 0, 1000)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            out_path = f.name
        try:
            result = export_mod.render(session, out_path)
            assert os.path.exists(out_path)
            # Should be shorter due to trimmed 1 second
            assert result["duration"] < 5.0
        finally:
            os.unlink(out_path)

    def test_export_complex(self, session):
        """Export with multiple regions and settings."""
        proj_mod.set_setting(session, "padding", 40)
        proj_mod.set_setting(session, "wallpaper", "solid_dark")

        tl_mod.add_zoom_region(session, 500, 2000, depth=4, focus_x=0.5, focus_y=0.5)
        tl_mod.add_speed_region(session, 3000, 4500, speed=1.5)
        tl_mod.add_trim_region(session, 0, 200)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            out_path = f.name
        try:
            result = export_mod.render(session, out_path)
            assert os.path.exists(out_path)
            assert result["file_size"] > 0
            assert result["width"] == 1920
            assert result["height"] == 1080
        finally:
            os.unlink(out_path)


# ── CLI Subprocess Tests ──────────────────────────────────────────────────

class TestCLISubprocess:
    def test_cli_help(self):
        result = subprocess.run(
            ["python3", "-m", "cli_anything.openscreen.openscreen_cli", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Openscreen CLI" in result.stdout

    def test_cli_version(self):
        result = subprocess.run(
            ["python3", "-m", "cli_anything.openscreen.openscreen_cli", "--version"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    def test_cli_export_presets(self):
        result = subprocess.run(
            ["python3", "-m", "cli_anything.openscreen.openscreen_cli",
             "--json", "export", "presets"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_cli_media_probe(self, test_video):
        result = subprocess.run(
            ["python3", "-m", "cli_anything.openscreen.openscreen_cli",
             "--json", "media", "probe", test_video],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["width"] == 1920
