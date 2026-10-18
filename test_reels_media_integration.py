"""Real local synthetic MP4s: test signals, not historical DJ pilots."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from media_evidence import MediaEvidenceError, inspect_reel
from video_factory import build_timeline, render_timeline

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg/FFprobe required")
class RealMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.temp=tempfile.TemporaryDirectory(); cls.root=Path(cls.temp.name)
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def clip(self,name,seconds=27,shape="720x1280",audio="sine=frequency=440:sample_rate=48000"):
        target=self.root/name
        args=["ffmpeg","-v","error","-y","-f","lavfi","-i",f"color=c=black:s={shape}:r=10"]
        if audio: args += ["-f","lavfi","-i",audio]
        args += ["-t",str(seconds),"-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p"]
        if audio: args += ["-c:a","aac","-b:a","96k"]
        subprocess.run([*args,str(target)],check=True,capture_output=True,timeout=60)
        return target

    def test_real_vertical_audible_27_seconds_is_only_mechanically_valid(self):
        r=inspect_reel(self.clip("synthetic-27.mp4"))
        self.assertEqual(r["status"],"MEDIA_TECHNICALLY_VALID"); self.assertFalse(r["editorial_approved"])
        self.assertFalse(r["audio"]["natural_dj_approved"])

    def test_legacy_four_tops_and_michael_jackson_duration_contract(self):
        for name in ("four-tops-synthetic-10.mp4","michael-jackson-synthetic-10.mp4"):
            with self.assertRaises(MediaEvidenceError): inspect_reel(self.clip(name,10))

    def test_missing_silent_audio_and_horizontal_video_rejected(self):
        for name,kwargs in (("missing.mp4",{"audio":None}),("silent.mp4",{"audio":"anullsrc=r=48000:cl=mono"}),
                            ("landscape.mp4",{"shape":"1280x720"})):
            with self.subTest(name=name),self.assertRaises(MediaEvidenceError): inspect_reel(self.clip(name,**kwargs))

    def test_10_second_audio_padded_to_27_is_rejected(self):
        signal="aevalsrc=if(lt(t\\,10)\\,0.15*sin(440*2*PI*t)\\,0):s=48000"
        with self.assertRaises(MediaEvidenceError): inspect_reel(self.clip("padded.mp4",audio=signal))

    def test_real_renderer_preserves_natural_duration_and_audio(self):
        source=self.clip("source.mp4")
        from PIL import Image
        scenes=[]
        for i,color in enumerate(("red","blue","green","orange","purple","yellow","gray","white")):
            p=self.root/f"scene-{i}.png"; Image.new("RGB",(720,1280),color).save(p); scenes.append(p)
        timeline=build_timeline(" ".join(["synthetic"]*64),source)
        target=self.root/"renderer-output.mp4"
        render_timeline(scenes=scenes[:len(timeline)],timeline=timeline,target=target,voiceover=source,
                        width=720,height=1280,fps=10,max_video_bytes=20*1024*1024)
        r=inspect_reel(target)
        self.assertTrue(27 <= r["duration_seconds"] <= 27.3)
        self.assertLess(abs(r["audio"]["decoded_seconds"]-27),.3)

if __name__=="__main__": unittest.main()
