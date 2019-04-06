#!/usr/bin/env python
#
# Copyright 2019 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# TODO: Create viz that displays generated Qiskit code for circuit
# TODO: Prevent error from occurring when circuit is empty
#
"""Create quantum circuits with Qiskit and Pygame"""

from pygame.locals import *

from model.circuit_grid_model import *
from containers.vbox import VBox
from utils.gamepad import *
from viz.statevector_grid import StatevectorGrid
from controls.circuit_grid import *

from utils.ball import *
from utils.score import *
from utils.fonts import *
from utils.parameters import *
from utils.scene import *
import random

if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')

pygame.init()

pygame.joystick.init()
num_joysticks = pygame.joystick.get_count()
if num_joysticks > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

# hardware acceleration to reduce flickering. Works only in fullscreen
flags = DOUBLEBUF|HWSURFACE|FULLSCREEN
screen = pygame.display.set_mode(WINDOW_SIZE, flags)

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill(BLACK)

pygame.font.init()

def update_paddle(circuit, circuit_grid_model, right_sprites, circuit_grid, statevector_grid):
    # Update visualizations
    # TODO: Refactor following code into methods, etc.
    circuit = circuit_grid_model.compute_circuit()
    statevector_grid.set_circuit(circuit, QUBIT_NUM, 100)
    right_sprites.arrange()
    circuit_grid.draw(screen)
    pygame.display.flip()

def main():
    pygame.display.set_caption('QPong')

    screen.fill(BLACK)

    # Prepare objects
    clock = pygame.time.Clock()
    oldclock = pygame.time.get_ticks()
    newclock = pygame.time.get_ticks()

    circuit_grid_model = CircuitGridModel(QUBIT_NUM, CIRCUIT_DEPTH)

    # the game crashes if the circuit is empty
    # initialize circuit with 3 identity gate at the end to prevent crash
    # identitiy gate are displayed by completely transparent PNG
    circuit_grid_model.set_node(0, CIRCUIT_DEPTH-1, CircuitGridNode(node_types.IDEN))
    circuit_grid_model.set_node(1, CIRCUIT_DEPTH-1, CircuitGridNode(node_types.IDEN))
    circuit_grid_model.set_node(2, CIRCUIT_DEPTH-1, CircuitGridNode(node_types.IDEN))

    circuit = circuit_grid_model.compute_circuit()

    statevector_grid = StatevectorGrid(circuit, QUBIT_NUM, 100)

    right_sprites = VBox(WIDTH_UNIT * 90, WIDTH_UNIT * 0, statevector_grid)

    ball = Ball()
    balls = pygame.sprite.Group()
    balls.add(ball)

    circuit_grid = CircuitGrid(0, ball.screenheight, circuit_grid_model)

    # computer paddle
    left_box = pygame.sprite.Sprite()
    left_box.image = pygame.Surface([WIDTH_UNIT, int(round(ball.screenheight / 2 ** QUBIT_NUM))])
    left_box.image.fill((255, 255, 255))
    left_box.image.set_alpha(255)
    left_box.rect = left_box.image.get_rect()
    left_box.rect.x = 9 * WIDTH_UNIT

    # player paddle for detection of collision. It is invisible on the screen
    right_box = pygame.sprite.Sprite()
    right_box.image = pygame.Surface([WIDTH_UNIT, int(round(ball.screenheight / 2 ** QUBIT_NUM))])
    right_box.image.fill((255, 0, 255))
    right_box.image.set_alpha(0)
    right_box.rect = right_box.image.get_rect()
    right_box.rect.x = right_sprites.xpos
    
    movingsprites = pygame.sprite.Group()
    movingsprites.add(ball)
    movingsprites.add(left_box)
    movingsprites.add(right_box)

    scene = Scene()

    pygame.display.flip()

    gamepad_repeat_delay = 100
    gamepad_neutral = True
    gamepad_pressed_timer = 0
    gamepad_last_update = pygame.time.get_ticks()

    measure_time = 100000

    # Main Loop
    #scene.start(screen, ball)
    going = scene.start(screen, ball)
    ball.ball_reset()
    while going:
        # set maximum frame rate
        clock.tick(60)

        screen.fill(BLACK)

        ball.update()

        for i in range(10, ball.screenheight, 2 * WIDTH_UNIT):  # draw dashed line
            pygame.draw.rect(screen, GRAY, (WINDOW_WIDTH // 2 - 5, i, 0.5 * WIDTH_UNIT, WIDTH_UNIT), 0)

        # Print the score
        text = PLAYER_FONT.render('Classical Computer', 1, GRAY)
        textpos = text.get_rect(center=(round(WINDOW_WIDTH * 0.25) + WIDTH_UNIT * 4.5, WIDTH_UNIT * 1.5))
        screen.blit(text, textpos)

        text = PLAYER_FONT.render('Quantum Computer', 1, GRAY)
        textpos = text.get_rect(center=(round(WINDOW_WIDTH * 0.75) - WIDTH_UNIT * 4.5, WIDTH_UNIT * 1.5))
        screen.blit(text, textpos)

        scoreprint = str(ball.check_score(0))
        text = SCORE_FONT.render(scoreprint, 1, GRAY)
        textpos = text.get_rect(center=(round(WINDOW_WIDTH * 0.25) + WIDTH_UNIT * 4.5, WIDTH_UNIT * 8))
        screen.blit(text, textpos)

        scoreprint = str(ball.check_score(1))
        text = SCORE_FONT.render(scoreprint, 1, GRAY)
        textpos = text.get_rect(center=(round(WINDOW_WIDTH * 0.75) - WIDTH_UNIT * 4.5, WIDTH_UNIT * 8))
        screen.blit(text, textpos)

        statevector_grid.display_statevector(QUBIT_NUM)
        right_sprites.draw(screen)
        movingsprites.draw(screen)
        circuit_grid.draw(screen)

        # Show game over screen if the score reaches WIN_SCORE, reset everything if replay == TRUE
        if ball.score.get_score(CLASSICAL_COMPUTER) >= WIN_SCORE:
            scene.gameover(screen, CLASSICAL_COMPUTER)
            scene.replay(screen, ball.score, circuit_grid_model, circuit_grid)
            update_paddle(circuit, circuit_grid_model, right_sprites, circuit_grid, statevector_grid)


        if ball.score.get_score(QUANTUM_COMPUTER) >= WIN_SCORE:
            scene.gameover(screen, QUANTUM_COMPUTER)
            scene.replay(screen, ball.score, circuit_grid_model, circuit_grid)
            update_paddle(circuit, circuit_grid_model, right_sprites, circuit_grid, statevector_grid)


        gamepad_move = False

        # computer paddle movement
        if pygame.time.get_ticks() - oldclock > 300:
            left_box.rect.y = ball.get_ypos()- statevector_grid.block_size/2+random.randint(-WIDTH_UNIT*4, WIDTH_UNIT*4)
            oldclock = pygame.time.get_ticks()

        # use joystick if it's connected
        if num_joysticks > 0:
            joystick_hat = joystick.get_hat(0)

            if joystick_hat == (0, 0):
                gamepad_neutral = True
                gamepad_pressed_timer = 0
            else:
                if gamepad_neutral:
                    gamepad_move = True
                    gamepad_neutral = False
                else:
                    gamepad_pressed_timer += pygame.time.get_ticks() - gamepad_last_update
            if gamepad_pressed_timer > gamepad_repeat_delay:
                gamepad_move = True
                gamepad_pressed_timer -= gamepad_repeat_delay
            if gamepad_move:
                if joystick_hat == (-1, 0):
                    move_update_circuit_grid_display(circuit_grid, MOVE_LEFT)
                elif joystick_hat == (1, 0):
                    move_update_circuit_grid_display(circuit_grid, MOVE_RIGHT)
                elif joystick_hat == (0, 1):
                    move_update_circuit_grid_display(circuit_grid, MOVE_UP)
                elif joystick_hat == (0, -1):
                    move_update_circuit_grid_display(circuit_grid, MOVE_DOWN)
            gamepad_last_update = pygame.time.get_ticks()

        # Check left thumbstick position
            left_thumb_x = joystick.get_axis(0)
            left_thumb_y = joystick.get_axis(1)

        # Handle Input Events
        for event in pygame.event.get():
            pygame.event.pump()

            if event.type == QUIT:
                going = False

            elif event.type == JOYBUTTONDOWN:
                if event.button == BTN_A:
                    # Place X gate
                    circuit_grid.handle_input_x()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_X:
                    # Place Y gate
                    circuit_grid.handle_input_y()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_B:
                    # Place Z gate
                    circuit_grid.handle_input_z()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_Y:
                    # Place Hadamard gate
                    circuit_grid.handle_input_h()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_RIGHT_TRIGGER:
                    # Delete gate
                    circuit_grid.handle_input_delete()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_RIGHT_THUMB:
                    # Add or remove a control
                    circuit_grid.handle_input_ctrl()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_LEFT_BUMPER:
                    # Update visualizations
                    # TODO: Refactor following code into methods, etc.
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)

            elif event.type == JOYAXISMOTION:
                # print("event: ", event)
                if event.axis == AXIS_RIGHT_THUMB_X and joystick.get_axis(AXIS_RIGHT_THUMB_X) >= 0.95:
                    circuit_grid.handle_input_rotate(np.pi / 8)
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_X and joystick.get_axis(AXIS_RIGHT_THUMB_X) <= -0.95:
                    circuit_grid.handle_input_rotate(-np.pi / 8)
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_Y and joystick.get_axis(AXIS_RIGHT_THUMB_Y) <= -0.95:
                    circuit_grid.handle_input_move_ctrl(MOVE_UP)
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_Y and joystick.get_axis(AXIS_RIGHT_THUMB_Y) >= 0.95:
                    circuit_grid.handle_input_move_ctrl(MOVE_DOWN)
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()

            elif event.type == KEYDOWN:
                index_increment = 0
                if event.key == K_ESCAPE:
                    going = False
                elif event.key == K_a:
                    circuit_grid.move_to_adjacent_node(MOVE_LEFT)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_d:
                    circuit_grid.move_to_adjacent_node(MOVE_RIGHT)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_w:
                    circuit_grid.move_to_adjacent_node(MOVE_UP)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_s:
                    circuit_grid.move_to_adjacent_node(MOVE_DOWN)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_x:
                    circuit_grid.handle_input_x()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_y:
                    circuit_grid.handle_input_y()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_z:
                    circuit_grid.handle_input_z()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_h:
                    circuit_grid.handle_input_h()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_SPACE:
                    circuit_grid.handle_input_delete()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_c:
                    # Add or remove a control
                    circuit_grid.handle_input_ctrl()
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_UP:
                    # Move a control qubit up
                    circuit_grid.handle_input_move_ctrl(MOVE_UP)
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_DOWN:
                    # Move a control qubit down
                    circuit_grid.handle_input_move_ctrl(MOVE_DOWN)
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_LEFT:
                    # Rotate a gate
                    circuit_grid.handle_input_rotate(-np.pi/8)
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_RIGHT:
                    # Rotate a gate
                    circuit_grid.handle_input_rotate(np.pi / 8)
                    circuit_grid.draw(screen)
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_TAB:
                    # Update visualizations
                    # TODO: Refactor following code into methods, etc.
                    update_paddle(circuit, circuit_grid_model, right_sprites,
                                  circuit_grid, statevector_grid)

        # check ball location and decide what to do
        ball.action()

        if ball.ball_action == MEASURE_RIGHT:
            #
            circuit = circuit_grid_model.compute_circuit()
            pos = statevector_grid.set_circuit_measure(circuit, QUBIT_NUM, 1)
            right_sprites.arrange()

            # paddle after measurement
            right_box.rect.y = pos * ball.screenheight/(2**QUBIT_NUM)

            measure_time=pygame.time.get_ticks()

        if pygame.sprite.spritecollide(right_box, balls, False):
            ball.bounce_edge()

        if pygame.sprite.spritecollide(left_box, balls, False):
            ball.bounce_edge()

        if pygame.time.get_ticks()-measure_time > 400:
            # refresh the screen a moment after measurement to update visual
            update_paddle(circuit, circuit_grid_model, right_sprites,
                          circuit_grid, statevector_grid)
            # add a buffer time before measure again
            measure_time = pygame.time.get_ticks() + 100000

        # Update the screen
        pygame.display.flip()

    pygame.quit()


def move_update_circuit_grid_display(circuit_grid, direction):
    circuit_grid.move_to_adjacent_node(direction)
    circuit_grid.draw(screen)
    pygame.display.flip()


if __name__ == '__main__':
    main()
