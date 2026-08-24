import os
from pathlib import Path
from winotify import Notification, audio

class NotificationManager:
    def __init__(self):
        self.app_id = "Danny Capture"

    def show_message(self, title: str, msg: str):
        """Generic toast without a file icon/actions (clipboard-only, errors)."""
        toast = Notification(app_id=self.app_id, title=title, msg=msg, duration="short")
        try:
            toast.show()
        except Exception as e:
            print(f"Failed to show notification: {e}")

    def show_capture_success(self, filepath: str, msg_override: str = None):
        # We need an absolute path to the icon, for now we will just not use an icon
        # or we could point it to the saved image itself
        
        path = Path(filepath)
        filename = path.name
        
        display_msg = msg_override if msg_override else filename
        
        toast = Notification(
            app_id=self.app_id,
            title="캡쳐 완료",
            msg=display_msg,
            duration="short",
            icon=str(path.absolute())
        )
        
        toast.set_audio(audio.Default, loop=False)
        
        # Add actions
        toast.add_actions(label="폴더 열기", launch=f"explorer.exe /select,\"{str(path.absolute())}\"")
        # toast.add_actions(label="편집기 열기", launch="...") # Editor launch logic will be handled within the app later
        
        try:
            toast.show()
        except Exception as e:
            print(f"Failed to show notification: {e}")
