extends Node3D

## Attach this script to the player's Camera3D.
@export var max_distance: float = 100.0
@export var damage: float = 25.0
@export var tracer_duration: float = 0.08
@export var tracer_color := Color(1.0, 0.82, 0.2, 1.0)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		_fire()

func _fire() -> void:
	var origin := global_position
	var direction := -global_transform.basis.z.normalized()
	var destination := origin + direction * max_distance
	var query := PhysicsRayQueryParameters3D.create(origin, destination)
	query.exclude = _get_player_rids()

	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	var end_point: Vector3 = destination
	if hit:
		end_point = hit.position
		var collider := hit.collider as Node
		print("Hitscan hit: %s at %s" % [collider.name if collider else "unknown", hit.position])
		if collider and collider.has_method("take_damage"):
			collider.call("take_damage", damage)
	else:
		print("Hitscan miss")

	_spawn_tracer(origin, end_point)

func _get_player_rids() -> Array[RID]:
	# Avoid the ray immediately colliding with the player's own physics body.
	var excluded: Array[RID] = []
	var node: Node = self
	while node:
		if node is CollisionObject3D:
			excluded.append(node.get_rid())
		node = node.get_parent()
	return excluded

func _spawn_tracer(start: Vector3, finish: Vector3) -> void:
	var host := get_tree().current_scene as Node3D
	if host == null:
		return

	var line := MeshInstance3D.new()
	line.name = "ShotTracer"
	var mesh := ImmediateMesh.new()
	mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	mesh.surface_add_vertex(host.to_local(start))
	mesh.surface_add_vertex(host.to_local(finish))
	mesh.surface_end()
	line.mesh = mesh

	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = tracer_color
	material.emission_enabled = true
	material.emission = tracer_color
	material.no_depth_test = true
	line.material_override = material
	host.add_child(line)
	await get_tree().create_timer(tracer_duration).timeout
	if is_instance_valid(line):
		line.queue_free()





