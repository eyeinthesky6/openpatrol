// OpenPatrol One parametric reference base, CERN-OHL-P-2.0
$fn=48; plate_x=360; plate_y=280; plate_t=6; wheel_clearance=75; hole=4.4;
module rounded_plate(){linear_extrude(plate_t) offset(r=18) square([plate_x-36,plate_y-36],center=true);}
module mounting_holes(){for(x=[-140,-100,-60,-20,20,60,100,140])for(y=[-100,-60,-20,20,60,100])translate([x,y,-1])cylinder(h=plate_t+2,d=hole);}
module wheel_relief(){for(y=[-plate_y/2,plate_y/2])translate([0,y,-1])cube([150,wheel_clearance,plate_t+2],center=true);}
difference(){rounded_plate();mounting_holes();wheel_relief();translate([0,0,-1])cylinder(h=plate_t+2,d=44);}
