import time


class RFIDReader:
    def __init__(self, slot_id):
        self.slot_id = slot_id

    def read_uid(self):
        return None


class PresenceSwitch:
    def __init__(self, slot_id):
        self.slot_id = slot_id

    def is_pressed(self):
        return False


class AudioSystem:
    def play_success(self):
        pass

    def play_error(self):
        pass


class LightSystem:
    def set_idle(self):
        pass

    def set_green(self):
        pass

    def flash_red(self, flashes=4, interval=0.2):
        pass


class VaultController:
    def __init__(
        self,
        expected_uid_by_slot,
        required_order,
        readers,
        switches,
        audio,
        lights,
        reset_delay=2.0,
        poll_interval=0.01
    ):
        self.expected_uid_by_slot = expected_uid_by_slot
        self.required_order = required_order
        self.readers = readers
        self.switches = switches
        self.audio = audio
        self.lights = lights
        self.reset_delay = reset_delay
        self.poll_interval = poll_interval

        self.slot_pressed = {slot_id: False for slot_id in readers}
        self.slot_uid = {slot_id: None for slot_id in readers}
        self.placement_order = []
        self.placement_timestamps_ms = {}
        self.locked_out = False

    def now_ms(self):
        return int(time.time() * 1000)

    def reset_state(self):
        self.slot_pressed = {slot_id: False for slot_id in self.readers}
        self.slot_uid = {slot_id: None for slot_id in self.readers}
        self.placement_order = []
        self.placement_timestamps_ms = {}
        self.locked_out = False
        self.lights.set_idle()

    def all_slots_filled(self):
        return all(self.slot_uid[slot_id] is not None for slot_id in self.readers)

    def capture_placement_events(self):
        for slot_id in self.readers:
            pressed = self.switches[slot_id].is_pressed()
            was_pressed = self.slot_pressed[slot_id]

            if pressed and not was_pressed:
                uid = self.readers[slot_id].read_uid()
                self.slot_uid[slot_id] = uid
                self.placement_order.append(slot_id)
                self.placement_timestamps_ms[slot_id] = self.now_ms()

            elif not pressed and was_pressed:
                self.handle_error()
                return

            self.slot_pressed[slot_id] = pressed

    def placed_correct_tokens(self):
        for slot_id, expected_uid in self.expected_uid_by_slot.items():
            if self.slot_uid[slot_id] != expected_uid:
                return False
        return True

    def placed_in_correct_order(self):
        return self.placement_order == self.required_order

    def handle_success(self):
        self.audio.play_success()
        self.lights.set_green()
        self.locked_out = True

    def handle_error(self):
        self.audio.play_error()
        self.lights.flash_red()
        time.sleep(self.reset_delay)
        self.reset_state()

    def evaluate(self):
        if not self.all_slots_filled():
            return

        if not self.placed_correct_tokens():
            self.handle_error()
            return

        if not self.placed_in_correct_order():
            self.handle_error()
            return

        self.handle_success()

    def tick(self):
        if not self.locked_out:
            self.capture_placement_events()
            self.evaluate()


class SimulatedRFIDReader(RFIDReader):
    def __init__(self, slot_id):
        super().__init__(slot_id)
        self.current_uid = None

    def read_uid(self):
        return self.current_uid


class SimulatedPresenceSwitch(PresenceSwitch):
    def __init__(self, slot_id):
        super().__init__(slot_id)
        self.pressed = False

    def is_pressed(self):
        return self.pressed


class SimulatedAudioSystem(AudioSystem):
    def __init__(self):
        self.events = []

    def play_success(self):
        self.events.append("audio_success")
        print("AUDIO: success")

    def play_error(self):
        self.events.append("audio_error")
        print("AUDIO: error")


class SimulatedLightSystem(LightSystem):
    def __init__(self):
        self.events = []

    def set_idle(self):
        self.events.append("lights_idle")
        print("LIGHTS: idle")

    def set_green(self):
        self.events.append("lights_green")
        print("LIGHTS: green")

    def flash_red(self, flashes=4, interval=0.2):
        self.events.append(f"lights_red_flash_{flashes}")
        print(f"LIGHTS: flashing red x{flashes}")


def build_simulator():
    readers = {
        1: SimulatedRFIDReader(1),
        2: SimulatedRFIDReader(2),
        3: SimulatedRFIDReader(3),
    }

    switches = {
        1: SimulatedPresenceSwitch(1),
        2: SimulatedPresenceSwitch(2),
        3: SimulatedPresenceSwitch(3),
    }

    expected_uid_by_slot = {
        1: "UID_ROOM_1",
        2: "UID_ROOM_2",
        3: "UID_ROOM_3",
    }

    required_order = [2, 1, 3]

    audio = SimulatedAudioSystem()
    lights = SimulatedLightSystem()

    controller = VaultController(
        expected_uid_by_slot=expected_uid_by_slot,
        required_order=required_order,
        readers=readers,
        switches=switches,
        audio=audio,
        lights=lights,
        reset_delay=0.1,
        poll_interval=0.01
    )

    return controller, readers, switches, audio, lights


def seat_token(controller, readers, switches, slot_id, uid):
    print(f"\nSeat token {uid} into slot {slot_id}")
    readers[slot_id].current_uid = uid
    switches[slot_id].pressed = True
    controller.tick()
    print_state(controller)


def remove_token(controller, readers, switches, slot_id):
    print(f"\nRemove token from slot {slot_id}")
    switches[slot_id].pressed = False
    readers[slot_id].current_uid = None
    controller.tick()
    print_state(controller)


def print_state(controller):
    print("slot_uid:", controller.slot_uid)
    print("placement_order:", controller.placement_order)
    print("locked_out:", controller.locked_out)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def test_success_case():
    print("\n=== TEST: SUCCESS CASE ===")
    controller, readers, switches, audio, lights = build_simulator()
    controller.reset_state()

    seat_token(controller, readers, switches, 2, "UID_ROOM_2")
    seat_token(controller, readers, switches, 1, "UID_ROOM_1")
    seat_token(controller, readers, switches, 3, "UID_ROOM_3")

    assert_true(controller.locked_out is True, "system locks out after success")
    assert_true("audio_success" in audio.events, "success audio played")
    assert_true("lights_green" in lights.events, "green lights set")


def test_wrong_order():
    print("\n=== TEST: WRONG ORDER ===")
    controller, readers, switches, audio, lights = build_simulator()
    controller.reset_state()

    seat_token(controller, readers, switches, 1, "UID_ROOM_1")
    seat_token(controller, readers, switches, 2, "UID_ROOM_2")
    seat_token(controller, readers, switches, 3, "UID_ROOM_3")

    assert_true(controller.locked_out is False, "system resets after wrong order")
    assert_true("audio_error" in audio.events, "error audio played")
    assert_true(any(event.startswith("lights_red_flash") for event in lights.events), "red flash triggered")


def test_wrong_uid():
    print("\n=== TEST: WRONG UID ===")
    controller, readers, switches, audio, lights = build_simulator()
    controller.reset_state()

    seat_token(controller, readers, switches, 2, "UID_ROOM_2")
    seat_token(controller, readers, switches, 1, "WRONG_UID")
    seat_token(controller, readers, switches, 3, "UID_ROOM_3")

    assert_true(controller.locked_out is False, "system resets after wrong uid")
    assert_true("audio_error" in audio.events, "error audio played")
    assert_true(any(event.startswith("lights_red_flash") for event in lights.events), "red flash triggered")


def test_remove_and_replace():
    print("\n=== TEST: REMOVE AND REPLACE ===")
    controller, readers, switches, audio, lights = build_simulator()
    controller.reset_state()

    seat_token(controller, readers, switches, 2, "UID_ROOM_2")
    seat_token(controller, readers, switches, 1, "UID_ROOM_1")
    remove_token(controller, readers, switches, 1)
    seat_token(controller, readers, switches, 1, "UID_ROOM_1")
    seat_token(controller, readers, switches, 3, "UID_ROOM_3")

    assert_true(controller.locked_out is False, "remove and replace changes order and fails")
    assert_true("audio_error" in audio.events, "error audio played after reorder")


if __name__ == "__main__":
    test_success_case()
    test_wrong_order()
    test_wrong_uid()
    test_remove_and_replace()
    print("\nAll simulator tests completed.")