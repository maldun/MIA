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
## Unknown names or types are logged and ignored, the current expression stays.
## After startup the bridge tells the host {"type": "ready"}.

signal handled(message: Dictionary, ok: bool)

var engine: ExpressionEngine
var _callback  # JavaScriptObject callback; keep the reference or it is freed

func setup(expression_engine: ExpressionEngine) -> void:
	engine = expression_engine
	if OS.has_feature("web"):
		_callback = JavaScriptBridge.create_callback(_on_js_message)
		JavaScriptBridge.get_interface("window").addEventListener("message", _callback)
		JavaScriptBridge.eval("window.parent.postMessage(JSON.stringify({type: 'ready'}), window.location.origin)")

## true if the page around the character is not the character itself (iframe in MIA's page)
static func is_embedded() -> bool:
	return OS.has_feature("web") and bool(JavaScriptBridge.eval("window.parent !== window"))

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
		"ready":
			ok = true  # our own message when the character is not embedded
		_:
			push_warning("unknown host message type '%s'" % message.get("type", ""))
	handled.emit(message, ok)
	return ok
