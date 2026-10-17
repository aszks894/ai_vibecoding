extends CanvasLayer

## Minimal fixed-screen crosshair. Add Crosshair.tscn to the active level.
@export var arm_length: float = 8.0
@export var gap: float = 4.0
@export var line_width: float = 2.0
@export var crosshair_color := Color.WHITE

func _ready() -> void:
	var center := Control.new()
	center.name = "Crosshair"
	center.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)

	_add_segment(center, Vector2(-gap - arm_length, 0), Vector2(-gap, 0))
	_add_segment(center, Vector2(gap, 0), Vector2(gap + arm_length, 0))
	_add_segment(center, Vector2(0, -gap - arm_length), Vector2(0, -gap))
	_add_segment(center, Vector2(0, gap), Vector2(0, gap + arm_length))

func _add_segment(parent: Control, from: Vector2, to: Vector2) -> void:
	var segment := ColorRect.new()
	segment.color = crosshair_color
	segment.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if is_equal_approx(from.y, to.y):
		segment.position = Vector2(minf(from.x, to.x), from.y - line_width * 0.5)
		segment.size = Vector2(absf(to.x - from.x), line_width)
	else:
		segment.position = Vector2(from.x - line_width * 0.5, minf(from.y, to.y))
		segment.size = Vector2(line_width, absf(to.y - from.y))
	parent.add_child(segment)
