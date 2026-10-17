class_name BackgroundManager
extends Node
## Custom background picture behind the character (ui/REQUIREMENTS.md 4.3).
## Pictures (png, jpg, webp) are taken from the "backgrounds" folder of MIA:
##  - in the browser from MIA's web server: GET /character-backgrounds.json lists them
##    ({"files": [...], "default": "name"}), GET /character-backgrounds/<name> delivers one;
##  - on the desktop (Godot editor, tools) directly from <repository>/backgrounds.
## Without pictures, or when the web server does not offer any, a plain colour is shown.
## The picture is scaled to cover the whole view (cropped, not stretched).

signal list_changed(names: Array, default_name: String)
signal background_changed(name: String)

const EXTENSIONS := ["png", "jpg", "jpeg", "webp"]
const MAX_SIZE := 2048
const LIST_ROUTE := "/character-backgrounds.json"
const FILE_ROUTE := "/character-backgrounds/"
const LOCAL_DIR := "../../backgrounds"  # relative to the Godot project (ui/godot)

var color := Color(0.86, 0.88, 0.92)
## desktop only: folder to read the pictures from instead of <repository>/backgrounds (tests)
var local_dir := ""
var names: Array = []
var default_name := ""
var current := ""

var _layer: CanvasLayer
var _picture: TextureRect

## Builds the canvas layer behind the 3D view (the environment shows canvas layers up to -1).
func setup() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = -1
	add_child(_layer)
	var plain := ColorRect.new()
	plain.color = color
	plain.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	plain.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(plain)
	_picture = TextureRect.new()
	_picture.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_picture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_picture.visible = false
	_layer.add_child(_picture)

## Looks for pictures and shows the default one (the picture named by the server, else the first).
func refresh() -> void:
	if OS.has_feature("web"):
		_fetch(_origin() + LIST_ROUTE, _on_list)
	else:
		var found: Array = []
		for f in DirAccess.get_files_at(_local_dir()):
			if EXTENSIONS.has(f.get_extension().to_lower()):
				found.append(f)
		found.sort()
		_set_list(found, found[0] if not found.is_empty() else "")

## Shows the picture with this name; "" (or an unknown name) shows the plain colour.
func show_background(name: String) -> void:
	if name.is_empty() or not names.has(name):
		if not name.is_empty():
			push_warning("unknown background '%s'" % name)
		_apply(null, "")
		return
	if OS.has_feature("web"):
		_fetch(_origin() + FILE_ROUTE + name.uri_encode(), _on_picture.bind(name))
	else:
		_apply(_decode(name, FileAccess.get_file_as_bytes(_local_dir().path_join(name))), name)

func _local_dir() -> String:
	if not local_dir.is_empty():
		return local_dir
	return ProjectSettings.globalize_path("res://").path_join(LOCAL_DIR).simplify_path()

func _set_list(files: Array, default_file: String) -> void:
	names = files
	default_name = default_file
	list_changed.emit(names, default_name)
	show_background(default_name)

func _apply(texture: Texture2D, name: String) -> void:
	_picture.texture = texture
	_picture.visible = texture != null
	current = name if texture != null else ""
	background_changed.emit(current)

## Turns the bytes of a picture file into a texture (too large pictures are scaled down).
func _decode(file_name: String, bytes: PackedByteArray) -> Texture2D:
	var image := Image.new()
	var err := ERR_FILE_UNRECOGNIZED
	match file_name.get_extension().to_lower():
		"png":
			err = image.load_png_from_buffer(bytes)
		"jpg", "jpeg":
			err = image.load_jpg_from_buffer(bytes)
		"webp":
			err = image.load_webp_from_buffer(bytes)
	if err != OK or image.is_empty():
		push_warning("cannot read background picture '%s'" % file_name)
		return null
	var longest := maxi(image.get_width(), image.get_height())
	if longest > MAX_SIZE:
		var f := float(MAX_SIZE) / float(longest)
		image.resize(int(image.get_width() * f), int(image.get_height() * f), Image.INTERPOLATE_BILINEAR)
	return ImageTexture.create_from_image(image)

# --- web: fetch from the server the page came from -------------------------------------------------

func _origin() -> String:
	return str(JavaScriptBridge.eval("window.location.origin"))

func _fetch(url: String, handler: Callable) -> void:
	var http := HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(func(result, code, _headers, body):
		http.queue_free()
		if result == HTTPRequest.RESULT_SUCCESS and code == 200:
			handler.call(body)
		else:
			push_warning("no background from %s (HTTP %s)" % [url, code]))
	if http.request(url) != OK:
		http.queue_free()

func _on_list(body: PackedByteArray) -> void:
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY or typeof(parsed.get("files")) != TYPE_ARRAY:
		return
	_set_list(parsed["files"], str(parsed.get("default", "")))

func _on_picture(body: PackedByteArray, name: String) -> void:
	_apply(_decode(name, body), name)
