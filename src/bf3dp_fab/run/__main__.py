import compas_rrc as rrc

from compas.data import json_load
import compas.geometry as cg

from bf3dp_fab import REPO_DIR

STEPPER_FORWARD_DO = "DO_9"
STEPPER_BACKWARDS_DO = "DO_10"
PRESSURE_DO = "DO_1"
TRAVEL_SPEED = 250
PRINT_SPEED = 250

EXTERNAL_AXES_DUMMY = rrc.ExternalAxes()

DRY_RUN = False

TOOL = "t_3dp_clay"
WOBJ = "w_3dp_clay"

FRAMES_FILE = REPO_DIR / "data" / "frames.json"

Z_HOP = 30

EXTRUSION_SPEED_MM_PER_SEC = 10.6
EXTRUSION_LENGTH = 28

PAUSE_AT_PT_SECONDS = EXTRUSION_LENGTH / EXTRUSION_SPEED_MM_PER_SEC

START_FROM = 449

HOME_POS = rrc.RobotJoints([0, 0, 0, 0, 0, 180])
RESET_POS = rrc.RobotJoints([0, 0, 10, 0, 20, 180])

OK_RANGES = ([-90, 90], [-360, 360], [-180, 180], [-100, 100], [-360, 360], [0, 360])


def is_robot_joints_ok(robot_joints: rrc.RobotJoints | [float]):
    for i, joint_and_range in enumerate(zip(robot_joints, OK_RANGES)):
        joint, range_ = joint_and_range
        min_, max_ = range_

        if not min_ < joint < max_:
            print(
                f"Joint number {i + 1} out of bounds. " +
                f"Min: {min_}, max: {max_}, actual: {joint}"
            )
            return False

    return True


if __name__ == "__main__":
    # Create Ros abb
    ros = rrc.RosClient()
    ros.run()

    # Create ABB abb
    abb = rrc.AbbClient(ros, "/rob1")
    print("Connected.")

    # Set Acceleration
    acc = 100  # Unit [%]
    ramp = 100  # Unit [%]
    abb.send(rrc.SetAcceleration(acc, ramp))

    # Set Max Speed
    override = 100  # Unit [%]
    max_tcp = 250  # Unit [mm/s]
    abb.send(rrc.SetMaxSpeed(override, max_tcp))

    # Reset signals
    abb.send(rrc.SetDigital(STEPPER_FORWARD_DO, 0))
    abb.send(rrc.SetDigital(STEPPER_BACKWARDS_DO, 0))
    abb.send(rrc.SetDigital(PRESSURE_DO, 0))

    abb.send(rrc.SetTool(TOOL))
    abb.send(rrc.SetWorkObject(WOBJ))

    # User message -> basic settings send to robot
    print("Tool, Wobj, Acc and MaxSpeed sent to robot")

    if not DRY_RUN:
        abb.send(rrc.SetDigital(PRESSURE_DO, 1))

    abb.send(
        rrc.MoveToJoints(HOME_POS, EXTERNAL_AXES_DUMMY, TRAVEL_SPEED, rrc.Zone.FINE)
    )

    frames_dict = json_load(FRAMES_FILE)

    extrude_frames = frames_dict["extrude_frames"]

    travel_frames = frames_dict["travel_frames"]

    if len(extrude_frames) != len(travel_frames):
        raise Exception("Lengths of extrude_frames and travel_frames do not match")

    n_extrusions = len(extrude_frames)

    highest_placed = None

    for i in range(START_FROM, n_extrusions):
        entry_frame = exit_frame = travel_frames[i]
        extrude_frame = extrude_frames[i]

        abb.send(
            rrc.MoveToFrame(entry_frame, TRAVEL_SPEED, rrc.Zone.Z1, rrc.Motion.JOINT)
        )

        abb.send(
            rrc.MoveToFrame(
                extrude_frame, PRINT_SPEED, rrc.Zone.FINE, rrc.Motion.LINEAR
            )
        )

        if not DRY_RUN:
            abb.send(rrc.SetDigital(STEPPER_FORWARD_DO, 1))

        abb.send(rrc.WaitTime(PAUSE_AT_PT_SECONDS))
        abb.send(rrc.SetDigital(STEPPER_FORWARD_DO, 0))

        if not DRY_RUN:  # retraction
            abb.send(rrc.SetDigital(STEPPER_BACKWARDS_DO, 1))
            abb.send(rrc.WaitTime(0.5))

        abb.send(rrc.SetDigital(STEPPER_BACKWARDS_DO, 0))

        msg = f"Extrusion number {i}/{n_extrusions} done."
        print(msg)
        abb.send(rrc.PrintText(msg))

        if not highest_placed:
            highest_placed = extrude_frame
        elif extrude_frame.point.z > highest_placed.point.z:
            highest_placed = extrude_frame.copy()

        abb.send(
            rrc.MoveToFrame(exit_frame, TRAVEL_SPEED, rrc.Zone.Z1, rrc.Motion.LINEAR)
        )

        # Get joints
        robot_joints, _ = abb.send_and_wait(rrc.GetJoints())

        if not is_robot_joints_ok(robot_joints):
            abb.send(rrc.PrintText("Resetting joint positions."))
            abb.send(
                rrc.MoveToJoints(
                    RESET_POS, EXTERNAL_AXES_DUMMY, TRAVEL_SPEED, rrc.Zone.Z10
                )
            )

        # this will raise IndexException when at end of list
        try:
            next_entry_frame = travel_frames[i + 1]
            midpoint_exit_next_entry = (entry_frame.point + next_entry_frame.point) / 2

            safe_midpoint_z = highest_placed.point.z + Z_HOP

            safe_midpoint = cg.Point(
                midpoint_exit_next_entry.x, midpoint_exit_next_entry.y, safe_midpoint_z
            )

            safe_midpoint_frame = cg.Frame(
                safe_midpoint,
                xaxis=next_entry_frame.xaxis,
                yaxis=next_entry_frame.yaxis,
            )

            abb.send_and_wait(
                rrc.MoveToFrame(
                    safe_midpoint_frame, TRAVEL_SPEED, rrc.Zone.Z5, rrc.Motion.JOINT
                )
            )
        except IndexError:
            pass

    abb.send(
        rrc.MoveToJoints(HOME_POS, EXTERNAL_AXES_DUMMY, TRAVEL_SPEED, rrc.Zone.FINE)
    )
    abb.send(rrc.SetDigital(PRESSURE_DO, 0))

    # Close abb
    ros.close()
    ros.terminate()
