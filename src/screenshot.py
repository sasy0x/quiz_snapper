import tkinter as tk
from PIL import ImageGrab
import pyautogui


class ScreenRegionSelector:
    def __init__(self):
        self.root = None
        self.overlay = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.region = None

    def _on_mouse_press(self, event):
        self.start_x = self.overlay.canvasx(event.x)
        self.start_y = self.overlay.canvasy(event.y)
        if self.rect:
            self.overlay.delete(self.rect)
        self.rect = None

    def _on_mouse_drag(self, event):
        cur_x = self.overlay.canvasx(event.x)
        cur_y = self.overlay.canvasy(event.y)
        if self.start_x is not None and self.start_y is not None:
            if self.rect:
                self.overlay.delete(self.rect)
            self.rect = self.overlay.create_rectangle(
                self.start_x, self.start_y, cur_x, cur_y,
                outline='#00FF00', width=3
            )

    def _on_mouse_release(self, event):
        end_x = self.overlay.canvasx(event.x)
        end_y = self.overlay.canvasy(event.y)

        if self.start_x is not None and self.start_y is not None:
            x1 = min(self.start_x, end_x)
            y1 = min(self.start_y, end_y)
            x2 = max(self.start_x, end_x)
            y2 = max(self.start_y, end_y)
            
            if x2 > x1 and y2 > y1:
                self.region = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
        
        self.root.quit()

    def select_region(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.wait_visibility(self.root)

        self.overlay = tk.Canvas(self.root, cursor="cross", bg="gray10", highlightthickness=0)
        self.overlay.pack(fill=tk.BOTH, expand=True)

        self.overlay.bind("<ButtonPress-1>", self._on_mouse_press)
        self.overlay.bind("<B1-Motion>", self._on_mouse_drag)
        self.overlay.bind("<ButtonRelease-1>", self._on_mouse_release)
        
        self.root.after(100, self.root.lift)
        self.root.mainloop()
        
        if self.root:
            self.root.destroy()
            self.root = None
            self.overlay = None
        
        return self.region


def capture_selected_region():
    selector = ScreenRegionSelector()
    region_coords = selector.select_region()

    if region_coords:
        try:
            x, y, w, h = region_coords
            bbox = (x, y, x + w, y + h)
            screenshot = ImageGrab.grab(bbox=bbox, all_screens=True)
            return screenshot
        except Exception as e:
            print(f"ImageGrab error: {e}")
            try:
                screenshot = pyautogui.screenshot(region=region_coords)
                return screenshot
            except Exception as e2:
                print(f"pyautogui error: {e2}")
                return None
    return None


if __name__ == '__main__':
    print("Select a screen region...")
    image = capture_selected_region()
    if image:
        image.save("selected_screenshot.png")
        print("Screenshot saved")
        image.show()
    else:
        print("Capture cancelled")