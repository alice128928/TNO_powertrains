def ev_state(time_step, avail, batteries, current_battery):
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
    status = []

    for i in range(len(avail)):

        car_status = avail[i][time_step]
        prev_charge = current_battery[i][time_step - 1] if time_step > 0 else 0

        if car_status == 2: # 2 means car is away
            status.append(0)
        elif car_status == 3: # means car is at the charging hub
            if prev_charge < batteries[i]: # it means the battery of the car is still empty
                status.append(1)
            else:
                status.append(5) # it means the battery of the car is full
        else:
            status.append(0) # safe check

    return status
