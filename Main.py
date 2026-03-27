import json
import math
import time
from tkinter import *
from PIL import Image, ImageTk


#time.sleep(5)
window = Tk()
canvas = Canvas(window, height=700, width=700)
canvas.pack()
canvas.configure(bg='white')
with open('roads.json') as jsonfile:
    graph = json.load(jsonfile) # {a: {b: [10 + L * 10 + H * 5, 0, 0] (current L and H cars number)}}
with open('Nodes_coords.json') as jsonfile:
    coords = json.load(jsonfile)
light_car = ImageTk.PhotoImage(Image.open('L_car.png').resize((30, 20), Image.Resampling.LANCZOS))
heavy_car = ImageTk.PhotoImage(Image.open('H_car.png').resize((30, 20), Image.Resampling.LANCZOS))
counter = 0

# drawing map
for node in graph.keys():
    for i in graph[node].keys():
        canvas.create_line(coords[node][0], coords[node][1], coords[i][0], coords[i][1],
                            width=2, fill='gray')

source = 'a' # graph['source']
destination = 'c' # graph['destination']


def position(x1, y1, x2, y2, arg): # to calc the position of time lines
    try:
        k = -1 * (x2 - x1) / (y2 - y1)
    except ZeroDivisionError:
        k = 1
    midx = (x1 + x2) / 2
    midy =(y1 + y2) / 2
    A = (x1 + x2) / 2
    B = midy - (midy - k * midx)
    x = (2 * A + 2 * B * k + arg * math.sqrt((2 * A + 2 * k * B) ** 2 - 4 * (1 + k ** 2) * (A ** 2 + B ** 2 - 600))) / (2 * (1 + k ** 2))
    return (x, k * x + midy - k * midx)

def read_chs(data: str): # number + L * a + H * b
    return [float(data.split()[0]), float(data.split()[4]),
            float(data.split()[8])] # [number, a, b]


class Car:

    def __init__(self, kind, canvas):
        self.canvas = canvas
        self.way = []
        self.kind = kind
        self.status = -1 # -1 - didn't start; 0 - on its way; 1 - reached destenation
        if kind == 'L':
            self.image = self.canvas.create_image(0, 0, image=light_car)
        else:
            self.image = self.canvas.create_image(0, 0, image=heavy_car)

    def moveto(self):
        for i in range(len(self.way)):
            if self.way[i][1] > 0:
                alpha = (self.way[i][2] - self.way[i][1]) / self.way[i][1]
                self.canvas.moveto(self.image, (coords[self.way[i - 1][0]][0] + alpha *
                                    coords[self.way[i][0]][0]) / (1 + alpha) - 15,
                                   (coords[self.way[i - 1][0]][1] + alpha *
                                    coords[self.way[i][0]][1]) / (1 + alpha) - 10)
                break


with open('cars.json') as jsonfile:
    cars = [Car(i, canvas) for i in json.load(jsonfile)] # list of L and H


def graph_calculation(graph: dict):
    new_time_lines = []
    traffic = list(filter(lambda x: x.status == 0, cars))
    graph = graph.copy()
    for node in graph.keys():
        for car in traffic:
            for car_node in range(len(car.way) - 1):
                if node in car.way[car_node] and car.way[car_node + 1][0] in graph[node].keys() and car.way[car_node + 1][1] > 0:
                    if car.kind == 'L':
                        graph[node][car.way[car_node + 1][0]][1] += 1
                        break
                    else:
                        graph[node][car.way[car_node + 1][0]][2] += 1
                        break
    for node in graph.keys():
        if graph[node]:
            for next_node in graph[node].keys():
                graph[node][next_node][0] = read_chs(graph[node][next_node][0])[0] \
                    + graph[node][next_node][1] * read_chs(graph[node][next_node][0])[1] \
                    + graph[node][next_node][2] * read_chs(graph[node][next_node][0])[2]
                for i in time_lines:
                    if i[1] == node and i[2] == next_node:
                        i[-2] = graph[node][next_node][0]
    for i in time_lines:
        canvas.delete(i[0])
        val = i[3]
        new_time_lines.append([canvas.create_text(*i[-1],
                             text=str(int(val)), fill='black', font=('Helvetica 22')),
                             i[1], i[2], [], i[-1]])
    return graph, new_time_lines


# draw nodes
for i in coords.keys():
    canvas.create_oval(coords[i][0] - 10, coords[i][1] - 10, coords[i][0] + 10, coords[i][1] + 10,
                        width=2, outline='black', fill='white')
    canvas.create_text(coords[i][0], coords[i][1],
                        text = i, font=("Arial", 15), fill='black')
    
# draw average time
time_lines = []
pairs_of_nodes = []
for node in graph.keys():
    arg = -1
    for i in graph[node].keys():
        pairs_of_nodes.append([node, i])
        if [i, node] in pairs_of_nodes:
            arg = 1
        time_lines.append([canvas.create_text(*position(coords[node][0],
                             coords[node][1], coords[i][0], coords[i][1], arg),
                             text='0', fill='black', font=('Helvetica 22')), node, i, [],
                             position(coords[node][0], coords[node][1], coords[i][0], coords[i][1], arg)])

while cars:
    counter += 1
    with open('roads.json') as jsonfile:
            graph = json.load(jsonfile) # {a: {b: [10 + L * 10 + H * 5, 0, 0] (current L and H cars number)}}
    if any(map(lambda x: x.status == -1, cars)):
        # preparing data
        unvisited, time_lines = graph_calculation(graph)
        shortest_distances = {}
        route = []
        path_nodes = {}

        # generating default setup and calculating edges
        for nodes in unvisited:
            shortest_distances[nodes] = math.inf
        shortest_distances[source] = 0.0

        # Dijkstra’s algorithm
        while unvisited:
            min_node = None
            for current_node in unvisited:
                if min_node is None:
                    min_node = current_node
                elif shortest_distances[min_node] > shortest_distances[current_node]:
                    min_node = current_node
            for (node, value) in unvisited[min_node].items():
                if value[0] + shortest_distances[min_node] < shortest_distances[node]:
                    shortest_distances[node] = value[0] + shortest_distances[min_node]
                    path_nodes[node] = [min_node, shortest_distances[min_node]]
            unvisited.pop(min_node)
        node, node_time = destination, shortest_distances[min_node]
            
        # storing data
        while node != source:
            route.insert(0, [node, node_time])
            node, node_time = path_nodes[node]
        for i in range(len(route) - 1, 0, -1):
            route[i][1] -= route[i - 1][1]
        route.insert(0, [source, 0])

        # new car start
        if counter % 10 == 0:
            for car in cars:
                if car.status == -1:
                    car.way = route
                    for node in car.way:
                        node.append(node[1])
                    car.status = 0
                    break
    
    # draw cars
    for car in filter(lambda x: x.status == 0,cars):
        car.moveto()

    # time decreasion for all driving cars (-1 iteration till all 0)
    for car in filter(lambda x: x.status == 0, cars):
        if all(map(lambda x: x[1] == 0, car.way)): # check if destination is reached
            cars.remove(car)
        else:
            for node in range(len(car.way)):
                if car.way[node][1] - 1 >= 0:
                    car.way[node][1] -= 1
                    break
                elif abs(car.way[node][1] - 1) < 1:
                    car.way[node][1] = 0
                    break

    time.sleep(0.01) # control the speed of simulation
    window.update()
window.mainloop()