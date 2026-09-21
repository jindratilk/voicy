#!/usr/bin/env python3
"""Package a previously signed/notarized Voicy.app in a styled macOS disk image.
Build dependency: pip install ds_store==1.3.2 mac_alias==2.2.3 pillow.
Does not modify the source application or manage signing credentials.
"""

import argparse, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ds_store import DSStore
from mac_alias import Alias


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    app = a.app.resolve()
    out = a.output.resolve()
    if not app.is_dir() or app.name != "Voicy.app":
        p.error("Expected a Voicy.app directory")
    if out.exists():
        p.error("Output exists; preserve existing releases")
    mount = Path("/Volumes/Voicy")
    if mount.exists():
        p.error("Eject the existing Voicy volume first")
    run("codesign", "--verify", "--deep", "--strict", str(app))
    run("xcrun", "stapler", "validate", str(app))
    with tempfile.TemporaryDirectory(prefix="voicy-dmg-") as tmp:
        tmp = Path(tmp)
        stage = tmp / "stage"
        stage.mkdir()
        run("cp", "-cR", str(app), str(stage / "Voicy.app"))
        (stage / "Applications").symlink_to("/Applications")
        (stage / ".background").mkdir()
        im = Image.new("RGB", (1320, 840), "#ececee")
        d = ImageDraw.Draw(im)
        font = lambda s: ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", s)
        d.text((660, 100), "voicy", font=font(58), fill="#171719", anchor="mm")
        d.text(
            (660, 171),
            "A clearer voice. One simple move.",
            font=font(25),
            fill="#77777d",
            anchor="mm",
        )
        d.line((570, 435, 747, 435), fill="#98989f", width=3)
        d.line((730, 418, 747, 435, 730, 452), fill="#98989f", width=3)
        d.text(
            (660, 690),
            "Drag Voicy to Applications",
            font=font(25),
            fill="#44444b",
            anchor="mm",
        )
        d.text(
            (660, 743),
            "Free. Local. Yours.",
            font=font(20),
            fill="#8a8a92",
            anchor="mm",
        )
        im.resize((660, 420), Image.Resampling.LANCZOS).save(
            stage / ".background/background.png"
        )
        icon = Path(__file__).resolve().parents[1] / "src-tauri/icons/icon.icns"
        run("cp", str(icon), str(stage / ".VolumeIcon.icns"))
        rw = tmp / "Voicy-rw.dmg"
        run(
            "hdiutil",
            "create",
            "-volname",
            "Voicy",
            "-srcfolder",
            str(stage),
            "-fs",
            "APFS",
            "-format",
            "UDRW",
            str(rw),
        )
        run("hdiutil", "attach", "-nobrowse", "-readwrite", str(rw))
        try:
            alias = Alias.for_file(str(mount / ".background/background.png"))
            alias.volume.disk_image_alias = (
                None  # Keep the build machine's path out of the installer.
            )
            with DSStore.open(str(mount / ".DS_Store"), "w+") as s:
                s["."]["bwsp"] = {
                    "ContainerShowSidebar": False,
                    "ShowPathbar": False,
                    "ShowSidebar": False,
                    "ShowStatusBar": False,
                    "ShowTabView": False,
                    "ShowToolbar": False,
                    "SidebarWidth": 0,
                    "WindowBounds": "{{160, 120}, {660, 420}}",
                }
                s["."]["icvp"] = {
                    "backgroundType": 2,
                    "backgroundColorRed": 1.0,
                    "backgroundColorGreen": 1.0,
                    "backgroundColorBlue": 1.0,
                    "backgroundImageAlias": alias.to_bytes(),
                    "showIconPreview": True,
                    "showItemInfo": False,
                    "textSize": 13.0,
                    "iconSize": 88.0,
                    "viewOptionsVersion": 1,
                    "gridSpacing": 100.0,
                    "gridOffsetX": 0.0,
                    "gridOffsetY": 0.0,
                    "labelOnBottom": True,
                    "arrangeBy": "none",
                }
                s["."]["vstl"] = ("type", b"icnv")
                s["."]["vSrn"] = ("long", 1)
                s["Voicy.app"]["Iloc"] = (175, 218)
                s["Applications"]["Iloc"] = (485, 218)
                s[".background"]["Iloc"] = (1000, 1000)
                s[".VolumeIcon.icns"]["Iloc"] = (1000, 1100)
            run("SetFile", "-a", "C", str(mount))
        finally:
            run("hdiutil", "detach", str(mount))
        out.parent.mkdir(parents=True, exist_ok=True)
        run("hdiutil", "convert", str(rw), "-format", "UDZO", "-o", str(out))
        print(out)


if __name__ == "__main__":
    main()
