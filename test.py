import pyatspi
from pyatspi import XY_SCREEN, XY_WINDOW
from pyatspi.state import STATE_VISIBLE, STATE_SHOWING

from tkinter import Tk, BOTH, Frame
from tkinter.ttk import Label, Style
from math import log, ceil
import itertools

class ClickableUiElement:
	def __init__(self, x, y, width, height, label):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.label = label

desktop = pyatspi.Registry.getDesktop(0)
visible_roles = ["push button", "toggle button"]
def find_children(element, depth=1):
	if depth > 4:
		return []

	results = []
	for m in element:
		if m is not None:
			point = m.get_position(XY_WINDOW)
			size = m.get_size()
			role_name = m.getRoleName()
			states = m.getState().getStates()

			if STATE_VISIBLE in states and STATE_SHOWING in states and role_name in visible_roles:
				print(f"position: ({point.x},{point.y}), size: ({size.x}, {size.y})")
				print(m)
				results.append(ClickableUiElement(point.x, point.y, size.x, size.y, role_name))
				
			results.extend(find_children(m, depth+1))
	return results


results = []
window_size = None
window_position = None
for app in desktop:
	for window in app:
		if window.getState().contains(pyatspi.STATE_ACTIVE):
			window_size = window.get_size()
			window_position = window.get_position(XY_SCREEN)
			print(f"{window.name}: position: ({window_position.x},{window_position.y}), size: ({window_size.x}, {window_size.y})")

			results = find_children(window)

results_count = len(results)
char_count = 26
#necessary_chars = ceil(log(results_count) / log(char_count))
necessary_chars = 2
char_sets = [ [ chr(char + 65) for char in range(char_count) ] for _ in range(necessary_chars) ]
char_combinations = itertools.product(*char_sets)
captions = [ "".join(combination) for combination in char_combinations ]
print(captions)

for result, caption in zip(results, captions):
	result.label = caption


if window_position is None or window_size is None:
	print("No active window found.")
	exit(0)

# make window transparent.
root = Tk()
root.overrideredirect(True)
root.wait_visibility(root)
root.wm_attributes("-alpha", 0.7)
w, h, x, y = window_size.x, window_size.y, window_position.x, window_position.y
root.geometry(f'{w}x{h}+{x}+{y}')

def keyup(e):
	print(f"up {e.char}")

def keydown(e):
    print(f"down {e.char}")


root.bind("<KeyPress>", keydown)
root.bind("<KeyRelease>", keyup)
root.bind("<Escape>", lambda e: root.destroy())

def create_label(x, y, width, height, caption):
	label_border = Frame(root, background="red")
	label = Label(label_border, text=caption)
	label.pack(fill="both", expand=True, padx=1, pady=1)

	label_border.place(x=x, y=y, width=width, height=height)


for result in results:
	create_label(result.x, result.y, result.width, result.height, result.label)

root.mainloop()

