"""
    Checks charging availability status for each car at a given time_step.

    Parameters:
    - time_step: integer representing the current time step (hour)
    - avail: list of numpy arrays, each representing availability status (2 = away, 3 = at charger)
    - batteries: list of maximum battery capacities for each car
    - current_battery: list of numpy arrays representing current battery charge per hour for each car

    Returns:
    - status :
        0 = not charging, means car is away and is not at the charging port
        1 = can charge, there is a battery capacity available for the car to continue charging
        5 = not charging, there is no battery capacity available for the car to continue charging
        status is an array, if there is one car it will return 1, 0 or 5. if there are more cars it will return
        an array with 0s,1s and 5s depending on the status of each car.
    """
def ev_state(time_step, avail, batteries, current_battery):
    status = []
    for i in range(len(avail)):
        epsilon = 1e-3
        car_status = avail[i][time_step]
        current_charge = current_battery[i][time_step]

        if car_status == 2:
            status.append(0)
        elif car_status == 3:
            if current_charge < batteries[i] - epsilon:
                status.append(1)
            else:
                status.append(5)
        else:
            status.append(0)

    return status
