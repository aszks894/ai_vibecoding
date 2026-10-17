extends CharacterBody3D

signal died(enemy: Node3D)

@export var max_health: float = 100.0
@export var detection_radius: float = 16.0
@export var melee_range: float = 1.7
@export var move_speed: float = 3.5
@export var attack_damage_per_second: float = 10.0
@export var gravity: float = 9.8
@export var target_path: NodePath

var health: float
var _target: Node3D
var _attack_accumulator: float = 0.0

func _ready() -> void:
	health = max_health
	if not target_path.is_empty():
		_target = get_node_or_null(target_path) as Node3D
	if _target == null:
		_target = get_tree().get_first_node_in_group("player") as Node3D

func _physics_process(delta: float) -> void:
	if not is_instance_valid(_target):
		_target = get_tree().get_first_node_in_group("player") as Node3D
		velocity.x = 0.0
		velocity.z = 0.0
		_apply_gravity(delta)
		move_and_slide()
		return

	var offset := _target.global_position - global_position
	offset.y = 0.0
	var distance := offset.length()
	velocity.x = 0.0
	velocity.z = 0.0

	if distance <= detection_radius:
		if distance > melee_range:
			var direction := offset.normalized()
			velocity.x = direction.x * move_speed
			velocity.z = direction.z * move_speed
			look_at(Vector3(_target.global_position.x, global_position.y, _target.global_position.z), Vector3.UP)
		else:
			_attack_accumulator += delta
			while _attack_accumulator >= 1.0:
				_attack_accumulator -= 1.0
				if _target.has_method("take_damage"):
					_target.call("take_damage", attack_damage_per_second)
	else:
		_attack_accumulator = 0.0

	_apply_gravity(delta)
	move_and_slide()

func _apply_gravity(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		velocity.y = 0.0

## Called by the hitscan shooter when a ray hits this enemy.
func take_damage(amount: float) -> void:
	if amount <= 0.0 or health <= 0.0:
		return
	health = maxf(health - amount, 0.0)
	print("Enemy took %.1f damage (%.1f HP left)" % [amount, health])
	if health <= 0.0:
		died.emit(self)
		queue_free()
