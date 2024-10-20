import pygame
import pymunk.pygame_util
import pymunk
from math import sin, radians, cos

#Car Specs
CAR_SIZE = (16.5, 8.5) # (Length, Width)
CAR_MASS = 5
CAR_SPEED = 5  # Impulse applied for forward/backward movement
CAR_TURN = 30  # Angular velocity for car turning
BRAKE_SPEED = 5  # Multiplier of CAR_SPEED for braking force
FREE_DECELERATION = 0.5  # Rate velocity decreases with no input
CAR_FRICTION = 0.5
CAR_COLOR = pygame.Color("green")

#Field Specs
FIELD_WIDTH = 426.72
FIELD_HEIGHT = 304.8
GOAL_HEIGHT = 81.28
GOAL_DEPTH = 25.4
SIDE_WALL = (FIELD_HEIGHT - GOAL_HEIGHT) / 2
FIELD_FRICTION = 0.3
FIELD_ELASTICITY = 0.5
FIELD_COLOR = pygame.Color("white")

#Ball Specs
BALL_MASS = 0.1
BALL_RADIUS = 6.85 / 2
BALL_POS = (FIELD_WIDTH + GOAL_DEPTH) / 2, FIELD_HEIGHT / 2 # Starting position of the ball (x, y)
BALL_ELASTICITY = 1
BALL_FRICTION = 0.5
BALL_DECELERATION = 0.1
BALL_COLOR = pygame.Color("blue")

#Sim Limits
MAX_SPEED = 200 # Max speed limit of the cars

class Car:
    """Class used to define each car in the simulator.
    :param x: x coordinate for the starting position of the car
    :type x: float
    :param y: y coordinate for the starting position of the car
    :type y: float
    :param space: Contains the :class: `pymunk.space` class object for calculating physical interactions
    :type space: class: `pymunk.space`
    :param angle: Starting rotational angle for the car (0 degrees is East)
    :type angle: float
    """
    def __init__(self, x, y, space, angle=0):
        """Constructor method"""
        self.body = pymunk.Body(CAR_MASS, pymunk.moment_for_box(CAR_MASS, CAR_SIZE))
        self.body.position = (x, y)
        self.body.angle = radians(angle)

        self.shape = pymunk.Poly.create_box(self.body, CAR_SIZE)
        self.shape.color = CAR_COLOR
        self.shape.friction = CAR_FRICTION

        self.space = space
        self.space.add(self.body, self.shape)

        self.steering = 0.0 # Rate of steering
        self.reverse = 1 # Stores which direction car moves, 1 for forwards and -1 for backwards

    def update(self, keys):
        """Calculates the needed motion of the car class called. Going to update later.
        :param keys: Contains :class: 'pygame.key.ScancodeWrapper' class to search for key inputs
        :type keys: class: 'pygame.key.ScancodeWrapper'
        """
        self.forward_direction = pymunk.Vec2d(cos(self.body.angle), sin(self.body.angle))
        
        self.impulse = pymunk.Vec2d(1, 0) * CAR_SPEED
        if keys[pygame.K_UP]:  # Move forward
            if self.reverse == 1:
                self.body.apply_impulse_at_local_point(self.impulse)
            else:
                self.body.apply_impulse_at_local_point(self.impulse * BRAKE_SPEED)
            if self.body.velocity.length < 5:
                self.reverse = 1
              
        elif keys[pygame.K_DOWN]:  # Move backward
            #self.body.velocity -= self.forward_direction
            if self.reverse == -1:
                self.body.apply_impulse_at_local_point(-self.impulse)
            else:
                self.body.apply_impulse_at_local_point(-self.impulse * BRAKE_SPEED)
            if self.body.velocity.length < 5:
                self.reverse = -1

        elif keys[pygame.K_SPACE]:
            if self.reverse == -1:
                self.body.apply_impulse_at_local_point(self.impulse * BRAKE_SPEED)
            elif self.reverse == 1:
                self.body.apply_impulse_at_local_point(-self.impulse * BRAKE_SPEED)
        else:
            #Simulates deceleration when no movement command is given
            self.body.velocity = (self.body.velocity.length - FREE_DECELERATION) * self.forward_direction * self.reverse
        
        # Turning the car
        self.turning_radius = CAR_SIZE[0] / sin(radians(CAR_TURN))
        if keys[pygame.K_LEFT]:  # Turn left
            self.body.angular_velocity = self.body.velocity.length / -self.turning_radius * self.reverse
        elif keys[pygame.K_RIGHT]:  # Turn right
            self.body.angular_velocity = self.body.velocity.length / self.turning_radius * self.reverse
        else:
            self.body.angular_velocity = 0  # Stop turning when no key is pressed
        
        # Reset drift: Set velocity to only move in the direction of the car's facing angle
        self.body.velocity = self.forward_direction * self.reverse * min(self.body.velocity.length, MAX_SPEED)
        #Prints current velocity
        #print("\rVelocity:{:0.2f}".format(self.body.velocity.length),end="")

class Ball:
    """Class used to define the soccer ball
    :param x: x coordinate for the starting position of the ball
    :type x: float
    :param y: y coordinate for the starting position of the ball
    :type y: float
    :param space: Contains the :class: `pymunk.space` class object for calculating physical interactions
    :type space: class: `pymunk.space`
    :param impulse: Starting impulse applied to the ball at object creation (defaults to no impulse)
    :type imlpulse: class: `pymunk.Vec2d`
    """
    def __init__(self, x:float, y:float, space:pymunk.Space, impulse:pymunk.Vec2d=pymunk.Vec2d(0,0)):
        """Constructor method"""
        self.inertia = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        self.body = pymunk.Body(BALL_MASS, self.inertia)
        self.body.position = x, y

        self.shape = pymunk.Circle(self.body, BALL_RADIUS)
        self.shape.friction = BALL_FRICTION
        self.shape.elasticity = BALL_ELASTICITY
        self.shape.color = BALL_COLOR

        self.space = space
        self.space.add(self.body, self.shape)

        self.body.apply_impulse_at_local_point(impulse)
    
    def decelerate(self):
        """Gradually reduces the velocity of the ball to simulate friction."""
        self.body.velocity = (self.body.velocity.length - BALL_DECELERATION) * self.body.velocity.normalized()
        #print("\rPos:{:0.2f}".format(self.body.position[0]),end="")
    
    def getPos(self):
        """Returns the ball's current x and y position
        :return: List of positional coordinates in :class:`pymunk.vec2d.Vec2d` format
        :rtype: :class:`pymunk.vec2d.Vec2d`
        """
        return self.body.position

class Game:
    """Gamestate object that handles simulation of physics.
    :param walls: Toggles the walls of the field on or off, no walls also disables goal checks
    :type walls: bool"""
    def __init__(self, walls:bool=False):
        """Constructor"""
        pygame.init()
        self.screen = pygame.display.set_mode((FIELD_WIDTH + GOAL_DEPTH, FIELD_HEIGHT))
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.clock = pygame.time.Clock()
        self.leftscore = 0
        self.rightscore = 0
        self.ticks = 60
        self.walls = walls
        self.exit = False
        self.gameSpace = pymunk.Space()
    
    def checkGoal(self, ball, leftgoal, rightgoal, topgoal, botgoal):
        """Checks to see if ball position is in a goal, then resets the field
        :param ball: Contains the :class:`rktl_sim.ball` class that will be checked into the 
        :param leftgoal:
        :param rightgoal:
        :param topgoal:
        :param botgoal:
        """
        if (ball.getPos()[0] < leftgoal):
            if (ball.getPos()[1] > topgoal) and (ball.getPos()[1] < botgoal):
                self.rightscore += 1
            self.reset()
        elif (ball.getPos()[0] > rightgoal):
            if (ball.getPos()[1] > topgoal) and (ball.getPos()[1] < botgoal):
                self.leftscore += 1
            self.reset()

    def reset(self):
        """Removes ball and car objects from the field."""
        for c in self.cars:
            self.gameSpace.remove(c.body, c.shape)
        self.gameSpace.remove(self.ball.body, self.ball.shape)
        self.addObjects()

    def addObjects(self):
        """Adds new ball and car objects to the field"""
        self.ball = Ball(BALL_POS[0], BALL_POS[1], self.gameSpace)
        self.cars = [
            Car((FIELD_WIDTH + GOAL_DEPTH) / 3, FIELD_HEIGHT / 2, self.gameSpace),
            Car(2 * (FIELD_WIDTH + GOAL_DEPTH) / 3, FIELD_HEIGHT / 2+50, self.gameSpace, 180)
        ]

    def run(self):
        """Main logic function to keep track of gamestate."""
        self.addObjects()
        
        # Walls in Field
        if self.walls:
            static_lines = [
                pymunk.Segment(self.gameSpace.static_body, (GOAL_DEPTH, 0.0), (FIELD_WIDTH, 0.0), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (FIELD_WIDTH, FIELD_HEIGHT), (GOAL_DEPTH, FIELD_HEIGHT), 0.0),

                pymunk.Segment(self.gameSpace.static_body, (FIELD_WIDTH, 0.0), (FIELD_WIDTH, SIDE_WALL), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (FIELD_WIDTH, SIDE_WALL), (FIELD_WIDTH + GOAL_DEPTH, SIDE_WALL), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (FIELD_WIDTH + GOAL_DEPTH, SIDE_WALL), (FIELD_WIDTH + GOAL_DEPTH, GOAL_HEIGHT + SIDE_WALL), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (FIELD_WIDTH, GOAL_HEIGHT + SIDE_WALL), (FIELD_WIDTH + GOAL_DEPTH, SIDE_WALL + GOAL_HEIGHT), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (FIELD_WIDTH, GOAL_HEIGHT + SIDE_WALL), (FIELD_WIDTH, FIELD_HEIGHT), 0.0),

                pymunk.Segment(self.gameSpace.static_body, (GOAL_DEPTH, SIDE_WALL), (GOAL_DEPTH, 0.0), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (GOAL_DEPTH, SIDE_WALL), (0, SIDE_WALL), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (0, SIDE_WALL), (0, GOAL_HEIGHT + SIDE_WALL), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (GOAL_DEPTH, GOAL_HEIGHT + SIDE_WALL), (0, SIDE_WALL + GOAL_HEIGHT), 0.0),
                pymunk.Segment(self.gameSpace.static_body, (GOAL_DEPTH, GOAL_HEIGHT + SIDE_WALL), (GOAL_DEPTH, FIELD_HEIGHT), 0.0),
            ]
            for l in static_lines:
                l.friction = FIELD_FRICTION
                l.elasticity = FIELD_ELASTICITY
            self.gameSpace.add(*static_lines)

        while not self.exit:
            self.dt = self.clock.get_time() / 1000

            # Quit event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit = True

            # User input
            pressed = pygame.key.get_pressed()

            # Logic
            for c in self.cars:
                c.update(pressed)
            self.ball.decelerate()
            if self.walls:
                self.checkGoal(self.ball, GOAL_DEPTH, FIELD_WIDTH, SIDE_WALL, SIDE_WALL + GOAL_HEIGHT)

            # Drawing
            print("\rLeft: ", self.leftscore, " Right: ", self.rightscore,end="")
            pygame.display.set_caption("fps: " + str(self.clock.get_fps()))
            self.screen.fill(pygame.Color("white"))
            self.gameSpace.debug_draw(self.draw_options)
            pygame.display.update()
            self.gameSpace.step(self.dt)

            self.clock.tick(self.ticks)
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
