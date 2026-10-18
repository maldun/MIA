class_name HostBridge
extends Node
## Receives commands from the page that hosts the character (MIA's chat page embeds this web export
## in an iframe and sends JSON strings through window.postMessage) and passes them to the
## expression engine, the central API.
##
## Messages (JSON object with a "type"):
##   {"type": "expression", "name": "happy"}     play an expression preset
##   {"type": "gesture", "name": "wave"}          play a gesture
##   {"type": "speaking", "value": true}          the character's voice is playing: the mouth moves
##   {"type": "background", "name": "room.jpg"}   show a picture of the backgrounds folder ("" = plain colour)
##   {"type": "viewport_inset", "left": 0, "right": 444, "top": 0, "bottom": 0, "width": 1440, "height": 900}
##                                                how many pixels of the window the page covers (chat panel); the camera
##                                                centers the character in the free area. width/height: size of the window.
##   {"type": "view", "name": "bust"}             camera view: body, bust or face
## Unknown names or types are logged and ignored, the current expression stays.
## After startup the bridge tells the host {"type": "ready"}.

signal handled(message: Dictionary, ok: bool)
## fractions of the window (0..MAX_INSET) the page covers on each side
signal inset_changed(left: float, right: float, top: float, bottom: float)
signal view_requested(view_name: String)

const MAX_INSET := 0.9
const VIEWS := ["body", "bust", "face"]

var engine: ExpressionEngine
var backgrounds: BackgroundManager
var _callback  # JavaScriptObject callback; keep the reference or it is freed

func setup(expression_engine: ExpressionEngine, background_manager: BackgroundManager = null) -> void:
	engine = expression_engine
	backgrounds = background_manager
	if OS.has_feature("web"):
		_callback = JavaScriptBridge.create_callback(_on_js_message)
		JavaScriptBridge.get_interface("window").addEventListener("message", _callback)
		JavaScriptBridge.eval("window.parent.postMessage(JSON.stringify({type: 'ready'}), window.location.origin)")

## true if the page around the character is not the character itself (iframe in MIA's page)
static func is_embedded() -> bool:
	return OS.has_feature("web") and bool(JavaScriptBridge.eval("window.parent !== window"))

## gives the keyboard focus to the canvas of the page (text fields need it in the browser; clicking is not always enough)
static func focus_canvas() -> void:
	if OS.has_feature("web"):
		JavaScriptBridge.eval("(function(){var c=document.querySelector('canvas'); if(c){window.focus(); c.focus();}})()")

## true if the URL has the given query parameter, e.g. ?menu
static func has_url_flag(flag: String) -> bool:
	return OS.has_feature("web") and str(JavaScriptBridge.eval("window.location.search")).contains(flag)

func _on_js_message(args: Array) -> void:
	var event = args[0]
	if str(event.origin) != str(JavaScriptBridge.eval("window.location.origin")):
		return  # only the page we were served from may talk to us
	handle_json(str(event.data))

func handle_json(text: String) -> bool:
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("host message is not a JSON object: %s" % text.left(80))
		return false
	return handle(parsed)

func handle(message: Dictionary) -> bool:
	var ok := false
	match message.get("type", ""):
		"expression":
			ok = engine.play(str(message.get("name", "")))
		"gesture":
			ok = engine.gestures.play(str(message.get("name", "")))
		"speaking":
			engine.set_speaking(bool(message.get("value", false)))
			ok = true
		"background":
			if backgrounds != null:
				backgrounds.show_background(str(message.get("name", "")))
				ok = true
		"viewport_inset":
			ok = _handle_inset(message)
		"view":
			var view_name := str(message.get("name", ""))
			if view_name in VIEWS:
				view_requested.emit(view_name)
				ok = true
		"ready":
			ok = true  # our own message when the character is not embedded
		_:
			push_warning("unknown host message type '%s'" % message.get("type", ""))
	handled.emit(message, ok)
	return ok

## pixels -> fractions of the window; refuses messages without a usable window size or with non-numbers
func _handle_inset(message: Dictionary) -> bool:
	var values := []
	for key in ["left", "right", "top", "bottom", "width", "height"]:
		var value = message.get(key, 0)
		if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
			push_warning("viewport_inset: '%s' is not a number" % key)
			return false
		values.append(float(value))
	if values[4] <= 0.0 or values[5] <= 0.0:
		push_warning("viewport_inset needs the window width and height")
		return false
	inset_changed.emit(clampf(values[0] / values[4], 0.0, MAX_INSET), clampf(values[1] / values[4], 0.0, MAX_INSET),
			clampf(values[2] / values[5], 0.0, MAX_INSET), clampf(values[3] / values[5], 0.0, MAX_INSET))
	return true
