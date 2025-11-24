import warp as wp
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random as rnd

# Initialize Warp
wp.init()

# Parameters
dt = 0.0001 # Time step
num_frames = 50000
radius = 0.154 
n=int(input("Number of balls : ")) #num of balls

# Initial positions and velocities (2D: XZ plane) are randomised
mass, pos, vel =[] , [] ,[] 
for i in range(n):
    mass.append(10**((rnd.random())*3+0.1))
    pos.append([4.8*rnd.random()*rnd.choice([-1,1]), 2.8*rnd.random()*rnd.choice([-1,1])])
    vel.append([200*((rnd.random())**(0.1))*rnd.choice([-1,1]), 50* ((rnd.random())**0.1)*rnd.choice([-1,1])])


"""
GPU kernel function for updating positions. NOTE: kernel functions don't return anything, they just change values
Inputs: positions, velocities and time step
"""
@wp.kernel
def update_positions(pos: wp.array(dtype=wp.vec2f), vel: wp.array(dtype=wp.vec2f), dt: float):
    tid = wp.tid() #start new thread
    pos[tid] += vel[tid] * dt  # x_new = x_old + v * dt


"""
Kernel function for collision between ball and boundary:
Inputs: mass (of balls), pos (positions of the balls), vel (velocities of balls), radius
"""
@wp.kernel
def boundary_collision(mass: wp.array(dtype=wp.float32), pos: wp.array(dtype=wp.vec2f), vel: wp.array(dtype=wp.vec2f), radius: float):
    tid=wp.tid() #new thread


    #Flip velocity in x-/ y-direction if ball is too far out in corresponding direction
    if abs(pos[tid][0]) > 5.0-radius:
        vel[tid][0]=-vel[tid][0]

    if abs(pos[tid][1]) > 3.0-radius:
        vel[tid][1]=-vel[tid][1]   

"""
GPU Kernel Function for collision between balls:
Inputs: mass, pos, vel, radius
Changes velocities
"""
@wp.kernel
def resolve_collision(mass: wp.array(dtype=wp.float32), pos: wp.array(dtype=wp.vec2f), vel: wp.array(dtype=wp.vec2f), radius: float): # type: ignore

    i, j = wp.tid() # Thread indices

    # Compute distance between spheres
    diff = pos[i] - pos[j]
    dist = wp.length(diff)

    #Compute distance between points after a small time nudge to avoid false positives for collision
    dist_nudge=wp.length(diff+(vel[i]-vel[j])*wp.float(dt/1000.0) )

    #i<j to avoid double-counting, dist<=2 r for proximity,
    # and dist_nudge < dist to avoid classifying balls moving apart after collision as new collision

    if i< j and dist <= 2.0 * radius and dist_nudge< dist:


        unit_v = diff /dist  #unit vector between spheres
        relative_velocity = vel[i] - vel[j]

        momentum =  unit_v* wp.dot(relative_velocity, unit_v) / (mass[i] + mass[j]) #formula from physics
        #changes velocities depending on mass
        vel[i] -= momentum * mass[j]
        vel[j] += momentum * mass[i]


# Convert to Warp GPU arrays
mass_gpu = wp.array(mass, dtype=wp.float32)
pos_gpu = wp.array(pos, dtype=wp.vec2f)
vel_gpu = wp.array(vel, dtype=wp.vec2f)

# Store positions for animation
positions=[[] for _ in range(n)]

#Main simulation loop
for step in range(num_frames):
    #Run simulation functions
    wp.launch(update_positions, dim=n, inputs=[pos_gpu, vel_gpu, dt])
    wp.launch(boundary_collision, dim=n, inputs=[mass_gpu, pos_gpu, vel_gpu, radius])
    wp.launch(resolve_collision, dim=(n,n), inputs=[mass_gpu, pos_gpu, vel_gpu, radius])

    # Convert GPU array to NumPy
    pos_np = pos_gpu.numpy()

    #update positions for animation   
    for i in range(n):
       positions[i].append([pos_np[i][0], pos_np[i][1]]) 

# Set up animation plot
fig = plt.figure()
ax = plt.axes(xlim=(-5, 5), ylim=(-3, 3), xlabel="X", ylabel = "Y" , title = "2D Collision Simulation")

# Create scatter plot for balls (or points)
points=[plt.plot([],[], "bo", markersize=10)[0] for _ in range(n)]


"""Initialisation function (for animation)
Inputs: None
Outputs: initialised points"""
def init():
    for point in points:
        point.set_data([],[])
    return points


""" Update function for animation"
Input: i= current frame number (int)
Output: points at current frame
"""
def update(i):
    #j is index of point
    for j, point in enumerate(points):
        point.set_data([positions[j][i][0]] , [positions[j][i][1]])

    return points

# Run animation using matplotlibs format

anim = animation.FuncAnimation(fig, update , init_func=init, frames=num_frames, interval=1.0, blit=True)


#show plot
plt.show()