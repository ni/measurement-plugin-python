from examples.game_of_life_Python.game_of_life_Python import measure, cancel

measure_response = measure()
i = 0
for response in measure_response:
    if i == 10:
        cancel()
    i= i+1
    print(response)