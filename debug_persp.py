import pygame
from math import *
import math as m
from basicHelpers import *
#from persp_proj_tests import *

WINDOW_SIZE =  800
ROTATE_SPEED = 3.141592 * 0.01
window = pygame.display.set_mode( (2560//2, 1440//2) )
clock = pygame.time.Clock()



FAR_LEFT = (-2.3, 0, 6.1)
FAR_RIGHT = ( 0.5, 0 , 6.1)
NEAR_LEFT = (-2.3, 0, 0.1)
NEAR_RIGHT = (0.5, 0, 0.1)

u1 = [-2.3, 0, 5.8]
u2 = [0.5, 0, 5.8]
u4 = (-2.3, 0, 0.1)
u3 =  (0.5, 0, 0.1)
#def connect_points(i, j, points):
#    pygame.draw.line(window, (255, 255, 255), (points[i][0], points[i][1]) , (points[j][0], points[j][1]))

points = [FAR_LEFT, FAR_RIGHT, NEAR_RIGHT, NEAR_LEFT]

# Main Loop


angle_x = angle_y = angle_z = 0
new = True

pp1 = persp_proj((1,0,1), (angle_x, angle_y, angle_z), (0,0,0))
print(pp1)
while True:
    clock.tick(60)
    window.fill((0,0,0))
    if new:
        snap_rot = [angle_x, angle_y - radians(60), angle_z]
        
        # _
        #|\|
        #
        #
        
        z_dist = 1 / abs(m.sin(snap_rot[1]))
        print('ZDIST',z_dist)
        FISH_LEFT_P1 = [ -2, 0, min(z_dist, 4.25) ]

        FISH_LEFT_P2 = [ -0.3,0,0.3 ]
        rot = (angle_x, angle_y, angle_z)


        
        pp1 = persp_proj(FISH_LEFT_P1, rot)  # persp_proj(FISH_LEFT_P1, rot )  
        
        pp2 = persp_proj(FISH_LEFT_P2, rot)  # persp_proj(FISH_LEFT_P1, rot )  
        pp1 = pp1[0]//2, pp1[1]//2
        pp2 = pp2[0]//2, pp2[1]//2
        #scan_line = Line(pp1, pp2)


        #pp1 = persp_proj( FAR_LEFT,)
        #pp2 = persp_proj(FAR_RIGHT,(angle_x, angle_y, angle_z))

        pygame.draw.circle(window, (0,0,255), pp1, 5)
        pygame.draw.circle(window, (0,0,255), pp2, 5)
        pygame.draw.line(window, (255, 255, 255),pp1,pp2)

        
        pp1 = persp_proj(u1, rot)  # persp_proj(FISH_LEFT_P1, rot )  
        
        pp2 = persp_proj(u2, rot)  # persp_proj(FISH_LEFT_P1, rot )
        pp1 = pp1[0]//2, pp1[1]//2
        pp2 = pp2[0]//2, pp2[1]//2
        #scan_line = Line(pp1, pp2)


        #pp1 = persp_proj( FAR_LEFT,)
        #pp2 = persp_proj(FAR_RIGHT,(angle_x, angle_y, angle_z))

        pygame.draw.circle(window, (0,0,255), pp1, 5)
        pygame.draw.circle(window, (0,0,255), pp2, 5)
        pygame.draw.line(window, (255, 0, 255),pp1,pp2)



        pp1 = persp_proj(u1, rot)  # persp_proj(FISH_LEFT_P1, rot )  
        
        pp2 = persp_proj(u4, rot)  # persp_proj(FISH_LEFT_P1, rot )
        pp1 = pp1[0]//2, pp1[1]//2
        pp2 = pp2[0]//2, pp2[1]//2
        #scan_line = Line(pp1, pp2)


        #pp1 = persp_proj( FAR_LEFT,)
        #pp2 = persp_proj(FAR_RIGHT,(angle_x, angle_y, angle_z))

        pygame.draw.circle(window, (0,0,255), pp1, 5)
        pygame.draw.circle(window, (0,0,255), pp2, 5)
        pygame.draw.line(window, (255, 0, 0),pp1,pp2)

        new = False
        pygame.display.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            angle_y = angle_x = angle_z = 0
        elif keys[pygame.K_a]:
            angle_y += ROTATE_SPEED
        elif keys[pygame.K_d]:
            angle_y -= ROTATE_SPEED      
        elif keys[pygame.K_w]:
            angle_x += ROTATE_SPEED
        elif keys[pygame.K_s]:
            angle_x -= ROTATE_SPEED
        elif keys[pygame.K_q]:
            angle_z -= ROTATE_SPEED
        elif keys[pygame.K_e]:
            angle_z += ROTATE_SPEED
        else:
            continue
        new = True
        print(angle_x, angle_y, angle_z)
        
    
