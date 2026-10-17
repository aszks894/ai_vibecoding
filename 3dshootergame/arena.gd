extends Node3D

## Gray-box arena dimensions, in meters.
@export var arena_size: float = 40.0
@export var wall_height: float = 6.0
@export var wall_thickness: float = 1.0

const FLOOR_COLOR := Color(0.32, 0.34, 0.36)
const WALL_COLOR := Color(0.48, 0.50, 0.52)
const COVER_COLOR := Color(0.38, 0.40, 0.42)

func _ready() -> void:
	_build_arena()

func _build_arena() -> void:
	# Floor is centered at the origin; its top surface is at y = 0.
	_add_box("Floor", Vector3(arena_size, 1.0, arena_size), Vector3(0.0, -0.5, 0.0), FLOOR_COLOR)

	var half := arena_size * 0.5
	var wall_center_y := wall_height * 0.5
	var long_wall := Vector3(arena_size, wall_height, wall_thickness)
	var end_wall := Vector3(wall_thickness, wall_height, arena_size)

	_add_box("NorthWall", long_wall, Vector3(0.0, wall_center_y, -half), WALL_COLOR)
	_add_box("SouthWall", long_wall, Vector3(0.0, wall_center_y, half), WALL_COLOR)
	_add_box("WestWall", end_wall, Vector3(-half, wall_center_y, 0.0), WALL_COLOR)
	_add_box("EastWall", end_wall, Vector3(half, wall_center_y, 0.0), WALL_COLOR)

	# Three simple waist-high cover pieces, spaced across the arena.
	_add_box("CoverBox", Vector3(3.0, 2.0, 2.0), Vector3(-8.0, 1.0, -5.0), COVER_COLOR)
	_add_cylinder("CoverPillar", 1.25, 3.0, Vector3(7.0, 1.5, -4.0), COVER_COLOR)
	_add_box("CoverBlock", Vector3(4.0, 2.5, 1.5), Vector3(1.0, 1.25, 8.0), COVER_COLOR)

func _add_box(object_name: String, size: Vector3, position: Vector3, color: Color) -> void:
	var body := StaticBody3D.new()
	body.name = object_name
	body.position = position
	add_child(body)

	var mesh_instance := MeshInstance3D.new()
	mesh_instance.name = "Mesh"
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _material(color)
	body.add_child(mesh_instance)

	var collision := CollisionShape3D.new()
	collision.name = "CollisionShape"
	var shape := BoxShape3D.new()
	shape.size = size
	collision.shape = shape
	body.add_child(collision)

func _add_cylinder(object_name: String, radius: float, height: float, position: Vector3, color: Color) -> void:
	var body := StaticBody3D.new()
	body.name = object_name
	body.position = position
	add_child(body)

	var mesh_instance := MeshInstance3D.new()
	mesh_instance.name = "Mesh"
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _material(color)
	body.add_child(mesh_instance)

	var collision := CollisionShape3D.new()
	collision.name = "CollisionShape"
	var shape := CylinderShape3D.new()
	shape.radius = radius
	shape.height = height
	collision.shape = shape
	body.add_child(collision)

func _material(color: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 1.0
	return material
