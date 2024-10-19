import pyatspi
from pyatspi import XY_SCREEN, XY_WINDOW
from pyatspi.state import STATE_VISIBLE, STATE_SHOWING

from tkinter import Tk, BOTH, Frame
from tkinter.ttk import Label, Style
from math import log, ceil
import itertools
import time

time.sleep(0)

class ClickableUiElement:
	def __init__(self, x, y, width, height, label, component, caption_element=None):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.label = label
		self.component = component
		self.caption_element = None

desktop = pyatspi.Registry.getDesktop(0)
visible_roles = ["push button", "toggle button"]
max_depth = 10

def has_actions(element):
	try:
		return element.queryAction().nActions > 0
	except:
		return False

def find_children(element, depth=1):
	if depth > max_depth:
		return []

	results = []
	print(len(element))
	for m in element:
		if m is not None:
			point = m.get_position(XY_WINDOW)
			size = m.get_size()
			role_name = m.getRoleName()
			states = m.getState().getStates()

			if STATE_VISIBLE in states and STATE_SHOWING in states and has_actions(m):
				print(f"position: ({point.x},{point.y}), size: ({size.x}, {size.y})")
				print(m)
				results.append(ClickableUiElement(point.x, point.y, size.x, size.y, role_name, m))
				
			results.extend(find_children(m, depth+1))
	return results


def find_position(element):
	for sub_element in element:
		states = sub_element.getState().getStates()

		if STATE_VISIBLE in states and STATE_SHOWING in states:	
			return sub_element.get_position(XY_SCREEN)
		
		return find_position(sub_element)

results = []
window_size = None
window_position = None
active_app = None
for app in desktop:
	print(app)
	for window in app:
		if window.getState().contains(pyatspi.STATE_ACTIVE):
			print(window)
			window_size = window.get_size()
			#window_position = find_position(window)
			window_position = window.get_position(XY_SCREEN)
			print(f"{window.name}: position: ({window_position.x},{window_position.y}), size: ({window_size.x}, {window_size.y})")
			active_app = app
			results = find_children(window)
			break

results_count = len(results)
char_count = 26
necessary_chars = ceil(log(results_count) / log(char_count))
char_sets = [ [ chr(char + 65) for char in range(char_count) ] for _ in range(necessary_chars) ]
char_combinations = itertools.product(*char_sets)
captions = [ "".join(combination) for combination in char_combinations ]

for result, caption in zip(results, captions):
	result.label = caption


if window_position is None or window_size is None:
	print("No active window found.")
	exit(0)

# make window transparent.
root = Tk()
title_bar_height = 34
#root.overrideredirect(True)
root.wait_visibility(root)
print(root.winfo_y())
root.wm_attributes("-alpha", 0.7)
w, h, x, y = window_size.x, window_size.y, window_position.x, window_position.y
root.geometry(f'{w}x{h}+{x}+{y}')
root.update_idletasks()
root.update()
print(root.winfo_y())
root.geometry(f'{w}x{h}+{x}+{y-title_bar_height}')


user_filter = ""
caption_to_element = {}

def update_captions():
	for caption in list(caption_to_element.keys()):
		if not caption.startswith(user_filter):
			label = caption_to_element[caption].caption_element
			label.destroy()
			print(f"Removing {caption}")
			del caption_to_element[caption]

def click_if_possible():
	if user_filter in caption_to_element:
		element:ClickableUiElement = caption_to_element[user_filter]
		print(f"Clicking on {element}")
		action = element.component.queryAction()
		
		print(f"Trigger action {action.getName(0)}")
		action.doAction(0)
		# close window
		root.destroy()
		return True
		
	return False
		
def keyup(e):
	print(f"up {e.char}")

def keydown(e):
	global user_filter
	print(f"down {e.char}")

	user_filter += e.char.upper()
	print(f"Updated filter: {user_filter}")
	
	if click_if_possible():
		return

	update_captions()


root.bind("<KeyPress>", keydown)
root.bind("<KeyRelease>", keyup)
root.bind("<Escape>", lambda e: root.destroy())

def create_label(x, y, width, height, caption):
	label_border = Frame(root, background="red")
	label = Label(label_border, text=caption)
	label.pack(fill="both", expand=True, padx=1, pady=1)

	label_border.place(x=x, y=y, width=width, height=height)
	return label_border


for result in results:
	label = create_label(result.x, result.y, result.width, result.height, result.label)
	result.caption_element = label
	caption_to_element[result.label] = result

def on_key_input(event):
	print(event)
	if event.type == pyatspi.KEY_RELEASED_EVENT:
		return False
		
	print(event.event_string)
	if event.event_string=='Esc':
		pyatspi.Registry.stop()
		root.destroy()
		return True
	else:
		user_filter += event.event_string.upper()
		print(f"Updated filter: {user_filter}")
		update_captions()

root.update()
#pyatspi.Registry.registerKeystrokeListener(on_key_input)
#pyatspi.Registry.registerKeystrokeListener(on_key_input, kind=(pyatspi.KEY_PRESSED_EVENT, pyatspi.KEY_RELEASED_EVENT))
#pyatspi.Registry.registerEventListenerWithApp(on_key_input, active_app, kind=(pyatspi.KEY_PRESSED_EVENT, pyatspi.KEY_RELEASED_EVENT))
#pyatspi.Registry.start()
#root.after(0, start_registry)
root.mainloop()

