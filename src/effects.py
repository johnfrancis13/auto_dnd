class EffectsManager:
    def __init__(self):
        self.effectss = []

    def add(self, effects):
        self.effects.append(effects)

    def remove(self, effects_type):
        self.effectss = [
            c for c in self.effects if not isinstance(c, effects_type)
        ]

    def apply_attack_effects(self, context):
        for effects in self.effects:
            effects.affects_attack(context)

    def apply_movement_effects(self, context):
        for effect in self.effects:
            effect.affects_movement(context)

    def apply_saving_throw_effects(self, context):
        for effect in self.effects:
            effect.affects_saving_throw(context)

class Effect:
    def affects_attack(self, context):
        pass

    def affects_movement(self, context):
        pass

    def affects_saving_throw(self, context):
        pass

# Individual effect classes
# Example effect
class reduce_movement(Effect):
    def affects_movement(self, context):
        return context.amount()
        
