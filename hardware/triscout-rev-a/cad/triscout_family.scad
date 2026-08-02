// TriScout Rev A family-style assembly preview — CERN-OHL-P-2.0
// Fabrication parts remain in triscout.scad; this file locks the exterior design language.
use <../../common/cad/family_style.scad>;
$fn=64;
track=300; wheel_d=100; wheel_w=40;
for(y=[-track/2,track/2]) translate([100,y,50]) op_wheel(wheel_d,wheel_w);
color("#18191B") translate([-145,0,28]) sphere(d=58);
translate([0,0,72]) op_ground_shell(350,255,118);
translate([-18,0,190]) op_lidar(68,36);
translate([162,0,122]) op_camera_bar(82,28,15);
translate([-80,102,172]) op_antenna(82,4.5);
translate([160,-92,135]) op_led_bar(44,6,3,"#F2F7FF");
translate([160,92,135]) op_led_bar(44,6,3,"#F2F7FF");
