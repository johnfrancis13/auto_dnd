class ConditionManager:
    def __init__(self, owner):
        self.owner = owner
        self.conditions = []

    def add(self, condition):
        self.conditions.append(condition)

    def remove(self, condition_type):
        self.conditions = [
            c for c in self.conditions if not isinstance(c, condition_type)
        ]

    def apply_attack_effects(self, context):
        for condition in self.conditions:
            condition.affects_attack(context)

    def apply_movement_effects(self, context):
        for condition in self.conditions:
            condition.affects_movement(context)

    def apply_saving_throw_effects(self, context):
        for condition in self.conditions:
            condition.affects_saving_throw(context)

class Condition:
    def affects_attack(self, context):
        pass

    def affects_movement(self, context):
        pass

    def affects_saving_throw(self, context):
        pass

# Individual condition classes

class Blinded(Condition):
    def affects_attack(self, context):
        context.grant_disadvantage()
        context.attackers_have_advantage()

class Charmed(Condition):
    def affects_attack(self, context):
        context.prevent_attacking_charmer()

class Deafened(Condition):
    pass

class Exhaustion(Condition):
    def __init__(self, level):
        self.level = level

    def affects_attack(self, context):
        if self.level >= 1:
            context.grant_disadvantage()

    def affects_movement(self, context):
        if self.level >= 2:
            context.set_speed(context.speed // 2)
        if self.level >= 5:
            context.set_speed(0)

class Frightened(Condition):
    def affects_attack(self, context):
        context.grant_disadvantage()

    def affects_movement(self, context):
        context.prevent_moving_closer()

class Grappled(Condition):
    def affects_movement(self, context):
        context.set_speed(0)

class Incapacitated(Condition):
    def affects_attack(self, context):
        context.prevent_actions()

class Invisible(Condition):
    def affects_attack(self, context):
        context.grant_advantage()
        context.attackers_have_disadvantage()

class Paralyzed(Condition):
    def affects_attack(self, context):
        context.prevent_actions()
        context.attackers_have_advantage()
        context.auto_fail_strength_dex_saves()

class Petrified(Condition):
    def affects_attack(self, context):
        context.prevent_actions()
        context.attackers_have_advantage()

    def affects_movement(self, context):
        context.set_speed(0)

class Poisoned(Condition):
    def affects_attack(self, context):
        context.grant_disadvantage()


class Prone(Condition):
    def affects_attack(self, context):
        context.melee_attackers_have_advantage()
        context.ranged_attackers_have_disadvantage()

    def affects_movement(self, context):
        context.require_half_movement_to_stand()

class Restrained(Condition):
    def affects_attack(self, context):
        context.grant_disadvantage()
        context.attackers_have_advantage()

    def affects_movement(self, context):
        context.set_speed(0)

class Stunned(Condition):
    def affects_attack(self, context):
        context.prevent_actions()
        context.attackers_have_advantage()
        context.auto_fail_strength_dex_saves()

    def affects_movement(self, context):
        context.set_speed(0)

class Unconscious(Condition):
    def affects_attack(self, context):
        context.prevent_actions()
        context.attackers_have_advantage()
        context.auto_fail_strength_dex_saves()
        context.melee_hits_are_critical()

    def affects_movement(self, context):
        context.set_speed(0)
