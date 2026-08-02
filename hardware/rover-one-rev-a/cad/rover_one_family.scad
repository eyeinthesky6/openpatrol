// Rover One Rev A family-style assembly preview — CERN-OHL-P-2.0
// Fabrication parts remain in rover_one.scad; this file locks the exterior design language.
use <../../common/cad/family_style.scad>;
$fn=64;
wheelbase=260; track=340; wheel_d=100; wheel_w=40;
for(x=[-wheelbase/2,wheelbase/2]) for(y=[-track/2,track/2]) translate([x,y,50]) op_wheel(wheel_d,wheel_w);
translate([0,0,78]) op_ground_shell(420,300,125);
translate([-45,0,202]) op_lidar(72,38);
translate([185,0,130]) rotate([0,0,0]) op_camera_bar(92,30,16);
translate([-80,112,182]) op_antenna(90,5);
translate([188,-105,145]) op_led_bar(54,7,3,"#F2F7FF");
translate([188,105,145]) op_led_bar(54,7,3,"#F2F7FF");
