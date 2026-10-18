class_name PresetApi
extends Node
## Client of MIA's preset API (presets_api.py): loads the presets shared by all devices and saves changes.
## In the browser it talks to the server the character came from; on the desktop to the address in the
## environment variable MIA_URL (e.g. http://localhost:8585). Without a server `available` stays false and the
## character keeps using the presets bundled with it.
##
## The version of the library is polled, so presets saved on one device show up on the others.

signal library_received(presets: Array, info: Dictionary)
signal availability_changed(available: bool)
## kind: "create", "update", "delete"; message: what to tell the user
signal operation_done(kind: String, ok: bool, message: String, data: Dictionary)
## the language model answered (or failed) for generate(): data has "id", "preset", "corrections", "closest", "seconds", "model"
signal generated(ok: bool, data: Dictionary, message: String)
## the closest existing preset for match_description(): data has "name", "score", "preset"
signal matched(data: Dictionary)

const POLL_SECONDS := 10.0
const TOKEN_HEADER := "X-MIA-Token"
const TOKEN_STORAGE_KEY := "mia_token"
const GENERATE_TIMEOUT := 180.0   # a local model may need a while to load

var base_url := ""
var token := ""
var available := false
var version := ""
var token_required := false
var protected_names: Array = []

var _timer: Timer
var _next_timeout := 0.0

## address of the server: the page's own origin in the browser, MIA_URL on the desktop ("" = none)
static func detect_base_url() -> String:
	if OS.has_feature("web"):
		return str(JavaScriptBridge.eval("window.location.origin"))
	return OS.get_environment("MIA_URL")

## the token is kept in the browser's local storage (not in the page); on the desktop it comes from MIA_TOKEN or the file MIA_TOKEN_FILE
static func stored_token() -> String:
	if not OS.has_feature("web"):
		var from_env := OS.get_environment("MIA_TOKEN")
		var file := OS.get_environment("MIA_TOKEN_FILE")   # e.g. MIA's data/editor_token.txt
		if from_env.is_empty() and not file.is_empty() and FileAccess.file_exists(file):
			return FileAccess.get_file_as_string(file).strip_edges()
		return from_env
	var value = JavaScriptBridge.eval("(function(){try{return window.localStorage.getItem('%s')||''}catch(e){return ''}})()" % TOKEN_STORAGE_KEY)
	return str(value)

static func store_token(value: String) -> void:
	if OS.has_feature("web"):
		JavaScriptBridge.eval("(function(){try{window.localStorage.setItem('%s', %s)}catch(e){}})()" % [TOKEN_STORAGE_KEY, JSON.stringify(value)])

func setup(url := "") -> void:
	base_url = (url if not url.is_empty() else detect_base_url()).rstrip("/")
	token = stored_token()
	_timer = Timer.new()
	_timer.wait_time = POLL_SECONDS
	_timer.timeout.connect(check_version)
	add_child(_timer)

## starts looking for changes of other devices
func start_polling() -> void:
	if _timer != null and not base_url.is_empty():
		_timer.start()

# --- reading -------------------------------------------------------------------------------------------

## loads all presets; the answer comes as library_received
func refresh() -> void:
	if base_url.is_empty():
		return
	_request(HTTPClient.METHOD_GET, "/api/presets", null, func(code: int, data):
		if code == 200 and typeof(data) == TYPE_DICTIONARY and typeof(data.get("presets")) == TYPE_ARRAY:
			_set_available(true)
			version = str(data.get("version", ""))
			token_required = bool(data.get("token_required", false))
			protected_names = data.get("protected", [])
			library_received.emit(data["presets"], data)
		else:
			_set_available(false))

## cheap check whether any preset changed since we loaded them
func check_version() -> void:
	if base_url.is_empty():
		return
	_request(HTTPClient.METHOD_GET, "/api/presets/version", null, func(code: int, data):
		if code == 200 and typeof(data) == TYPE_DICTIONARY:
			if not available or str(data.get("version", "")) != version:
				refresh()
		else:
			_set_available(false))

# --- changing -------------------------------------------------------------------------------------------

func create(preset: Dictionary) -> void:
	_write("create", HTTPClient.METHOD_POST, "/api/presets", preset)

## overwrites the preset `old_name`; a different name inside `preset` renames it
func update(old_name: String, preset: Dictionary) -> void:
	_write("update", HTTPClient.METHOD_PUT, "/api/presets/" + old_name.uri_encode(), preset)

func delete(preset_name: String, force := false) -> void:
	_write("delete", HTTPClient.METHOD_DELETE, "/api/presets/" + preset_name.uri_encode() + ("?force=1" if force else ""), null)

# --- expressions from a description ---------------------------------------------------------------------

## asks the language model for an expression (answer: generated); the result is not saved, keep it with create()
func generate(description: String) -> void:
	if not available:
		generated.emit(false, {}, "Offline: the server cannot be reached.")
		return
	_next_timeout = GENERATE_TIMEOUT
	_request(HTTPClient.METHOD_POST, "/api/expression/generate", {"description": description}, func(code: int, data):
		var info: Dictionary = data if typeof(data) == TYPE_DICTIONARY else {}
		if code == 200 and typeof(info.get("preset")) == TYPE_DICTIONARY:
			generated.emit(true, info, "")
		elif code == 0:
			generated.emit(false, {}, "The server cannot be reached.")
		else:
			generated.emit(false, {}, str(info.get("error", "HTTP %d" % code))))

## instant answer without the language model: the existing preset that fits the description best (answer: matched)
func match_description(description: String) -> void:
	if not available:
		return
	_request(HTTPClient.METHOD_POST, "/api/expression/match", {"description": description}, func(code: int, data):
		if code == 200 and typeof(data) == TYPE_DICTIONARY:
			matched.emit(data))

## tells the server what the user did with a generated expression: "keep", "edit" (with the saved preset) or "reject"
func send_feedback(request_id: String, decision: String, preset := {}) -> void:
	if not available:
		return
	var body := {"id": request_id, "decision": decision}
	if not preset.is_empty():
		body["preset"] = preset
	_request(HTTPClient.METHOD_POST, "/api/expression/feedback", body, func(_code: int, _data): pass)

func _write(kind: String, method: int, path: String, body) -> void:
	if not available:
		operation_done.emit(kind, false, "Offline: the server cannot be reached, nothing was saved.", {})
		return
	_request(method, path, body, func(code: int, data):
		var ok := code >= 200 and code < 300
		var message := ""
		var info: Dictionary = data if typeof(data) == TYPE_DICTIONARY else {}
		if ok:
			message = _success_message(kind, info)
		elif code == 401:
			token_required = true
			message = unauthorized_message()
		elif code == 0:
			_set_available(false)
			message = "The server cannot be reached."
		else:
			message = str(info.get("error", "HTTP %d" % code))
		operation_done.emit(kind, ok, message, info))

## what to tell the user when the server refuses a change because of the token (none entered, or a wrong or outdated one)
func unauthorized_message() -> String:
	if token.is_empty():
		return "A token is needed to change presets: paste it into the Token field below (it is in MIA's data/editor_token.txt and printed when MIA starts)."
	return "The token was not accepted (wrong or outdated). Paste the current one into the Token field below: data/editor_token.txt in MIA's folder, also printed when MIA starts."

func _success_message(kind: String, info: Dictionary) -> String:
	var corrections: Array = info.get("corrections", [])
	var text: String = {"create": "Saved as new preset.", "update": "Saved.", "delete": "Deleted."}.get(kind, "Done.")
	if not corrections.is_empty():
		text += " Corrected: " + "; ".join(PackedStringArray(corrections))
	return text

# --- transport (replaced in tests) ----------------------------------------------------------------------

## done(code, parsed_json); code 0 = no connection
func _request(method: int, path: String, body, done: Callable) -> void:
	var http := HTTPRequest.new()
	http.timeout = _next_timeout
	_next_timeout = 0.0
	add_child(http)
	var headers := PackedStringArray(["Accept: application/json"])
	if body != null:
		headers.append("Content-Type: application/json")
	if not token.is_empty():
		headers.append("%s: %s" % [TOKEN_HEADER, token])
	http.request_completed.connect(func(result, code, _headers, bytes):
		http.queue_free()
		if result != HTTPRequest.RESULT_SUCCESS:
			done.call(0, null)
			return
		done.call(code, JSON.parse_string(bytes.get_string_from_utf8())))
	var payload := "" if body == null else JSON.stringify(body)
	if http.request(base_url + path, headers, method, payload) != OK:
		http.queue_free()
		done.call(0, null)

func _set_available(value: bool) -> void:
	if value != available:
		available = value
		availability_changed.emit(available)
