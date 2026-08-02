// OpenPatrol Sentinel Rev A — CERN-OHL-P-2.0
// Wheeled sentry with masked sensor head and 520 mm telescoping mast.
// Engineering release; physical stability, mast and stopping tests remain mandatory.
use <../../common/cad/family_style.scad>;
$fn=64;
part="assembly"; // assembly, lower_deck, upper_deck, torso_base, mast_base, head_plate, cover_front, cover_side, bumper_bar, motor_saddle, mast_bushing, mask_frame, head_shell, corner_block, cable_guide, led_bezel
flat=false;
mast_extension=1; // 0 retracted, 1 fully extended for assembly preview
plate_t=3;
plate_x=430;
plate_y=320;
wheel_d=125;
wheel_w=45;
wheelbase=280;
track=360;
deck_gap=92;
torso_h=430;
retracted_sensor_h=980;
travel=520;

module rounded_plate(x,y,t,r=18){linear_extrude(t) offset(r=r) square([x-2*r,y-2*r],center=true);}
module slot(length=18,width=5,height=10){hull(){translate([-length/2+width/2,0,0]) cylinder(h=height,d=width);translate([length/2-width/2,0,0]) cylinder(h=height,d=width);}}
module payload_grid(xs=180,ys=120,pitch=20,h=10){for(x=[-xs/2:pitch:xs/2]) for(y=[-ys/2:pitch:ys/2]) translate([x,y,-1]) cylinder(h=h,d=4.4);}

module lower_deck(){
  difference(){
    rounded_plate(plate_x,plate_y,plate_t,24); payload_grid(180,120,20,plate_t+2);
    for(x=[-wheelbase/2,wheelbase/2]) for(y=[-122,122]){
      translate([x-28,y,-1]) slot(24,5,plate_t+2);translate([x+28,y,-1]) slot(24,5,plate_t+2);
    }
    for(y=[-52,52]) translate([-15,y,-1]) slot(175,8,plate_t+2); // battery straps
    translate([0,0,-1]) rounded_plate(100,62,plate_t+2,9);
    for(x=[-178,178]) for(y=[-128,128]) translate([x,y,-1]) cylinder(h=plate_t+2,d=5.2);
    for(x=[-205,205]) for(y=[-92,92]) translate([x,y,-1]) cylinder(h=plate_t+2,d=5.2);
  }
}
module upper_deck(){
  difference(){
    rounded_plate(380,280,plate_t,22);payload_grid(260,180,20,plate_t+2);
    for(x=[-29,29]) for(y=[-24.5,24.5]) translate([x-70,y,-1]) cylinder(h=plate_t+2,d=3);
    for(x=[-42,42]) for(y=[-31,31]) translate([x+105,y,-1]) slot(12,4.2,plate_t+2);
    for(x=[-155,155]) for(y=[-105,105]) translate([x,y,-1]) cylinder(h=plate_t+2,d=5.2);
    translate([0,-112,-1]) rounded_plate(82,24,plate_t+2,6);
  }
}
module torso_base(){
  difference(){
    rounded_plate(250,220,5,18);
    for(x=[-92,92]) for(y=[-77,77]) translate([x,y,-1]) cylinder(h=8,d=6.2);
    for(x=[-55,55]) for(y=[-45,45]) translate([x,y,-1]) slot(18,5.2,8);
    translate([0,0,-1]) rounded_plate(100,82,8,10);
  }
}
module mast_base(){
  difference(){
    rounded_plate(150,150,6,16);
    rounded_plate(92,92,10,8);
    for(x=[-62,62]) for(y=[-62,62]) translate([x,y,-1]) cylinder(h=10,d=8.2);
  }
}
module head_plate(){
  difference(){rounded_plate(170,92,3,12);for(x=[-65,65]) for(y=[-28,28]) translate([x,y,-1]) slot(15,4.2,5);translate([0,0,-1]) rounded_plate(68,44,5,7);}
}
module motor_saddle(){
  difference(){union(){cube([56,22,20],center=true);translate([0,0,10]) rotate([90,0,0]) cylinder(h=22,d=48,center=true);}translate([0,0,10]) rotate([90,0,0]) cylinder(h=26,d=38.5,center=true);for(x=[-23,23]) translate([x,0,-13]) cylinder(h=32,d=5.2);translate([0,0,20]) cube([5,26,22],center=true);}
}
module mast_bushing(){
  difference(){op_round_box([104,104,28],r=10);op_round_box([84.8,84.8,34],r=7);for(x=[-44,44]) for(y=[-44,44]) translate([x,y,-20]) cylinder(h=40,d=5.2);}
}
module mask_frame(){
  difference(){op_round_box([194,114,90],r=16);translate([-55,0,0]) op_round_box([96,92,62],r=11);translate([34,0,0]) op_round_box([92,88,68],r=12);}
}
module head_shell(){
  difference(){op_round_box([194,114,90],r=16);translate([-5,0,0]) op_round_box([174,96,72],r=12);translate([-100,0,0]) cube([20,86,58],center=true);}
}
module cover_front(){
  difference(){linear_extrude(2) offset(r=20) square([230,410],center=true);translate([0,-82,-1]) rounded_plate(22,94,4,7);for(y=[-150:30:150]) translate([0,y,-1]) slot(30,4,4);for(x=[-92,92]) for(y=[-185,185]) translate([x,y,-1]) cylinder(h=4,d=4.2);}
}
module cover_side(){
  difference(){linear_extrude(2) offset(r=18) square([210,410],center=true);for(y=[-150:30:150]) translate([0,y,-1]) slot(26,4,4);for(x=[-82,82]) for(y=[-185,185]) translate([x,y,-1]) cylinder(h=4,d=4.2);}
}
module bumper_bar(){difference(){rounded_plate(380,22,3,6);for(x=[-175,175]) translate([x,0,-1]) cylinder(h=5,d=5.2);}}
module corner_block(){difference(){cube([28,28,34],center=true);rotate([0,90,0]) cylinder(h=38,d=4.2,center=true);rotate([90,0,0]) cylinder(h=38,d=4.2,center=true);cylinder(h=42,d=4.2,center=true);}}
module cable_guide(){difference(){cube([36,14,12],center=true);translate([0,0,3]) rotate([90,0,0]) cylinder(h=18,d=9,center=true);for(x=[-14,14]) translate([x,0,-9]) cylinder(h=18,d=3.4);}}
module led_bezel(){difference(){op_round_box([10,7,92],r=4);op_round_box([5,10,78],r=2);}}
module wheel(x,y){translate([x,y,62.5]) op_wheel(wheel_d,wheel_w);}

module assembly(){
  color("silver") translate([0,0,62]) lower_deck();
  color("gainsboro") translate([0,0,62+deck_gap]) upper_deck();
  for(x=[-wheelbase/2,wheelbase/2]) for(y=[-track/2,track/2]) wheel(x,y);
  color("#FFB343") for(x=[-208,208]) translate([x,0,78]) rotate([0,0,90]) bumper_bar();
  // Shared ground-family base shell.
  translate([0,0,145]) op_ground_shell(430,315,120);
  color("#E7E4DC") translate([0,0,222]) torso_base();
  color("#E7E4DC") translate([0,0,455]) op_round_box([250,220,430],r=26);
  color("#25282B") translate([0,0,687]) mast_base();
  translate([0,0,690]) op_telescoping_mast(290,travel,mast_extension);
  head_z=retracted_sensor_h+travel*mast_extension;
  translate([0,0,head_z]) rotate([0,0,0]) op_masked_head([190,110,85]);
  translate([-125,0,520]) op_led_bar(74,7,4,"#2F8BFF");
  translate([70,92,575]) op_antenna(110,5);
  translate([205,-105,178]) op_led_bar(38,6,3,"#FFB343");
  translate([205,105,178]) op_led_bar(38,6,3,"#FFB343");
}
module selected(){
  if(part=="lower_deck") lower_deck();
  else if(part=="upper_deck") upper_deck();
  else if(part=="torso_base") torso_base();
  else if(part=="mast_base") mast_base();
  else if(part=="head_plate") head_plate();
  else if(part=="cover_front") cover_front();
  else if(part=="cover_side") cover_side();
  else if(part=="bumper_bar") bumper_bar();
  else if(part=="motor_saddle") motor_saddle();
  else if(part=="mast_bushing") mast_bushing();
  else if(part=="mask_frame") mask_frame();
  else if(part=="head_shell") head_shell();
  else if(part=="corner_block") corner_block();
  else if(part=="cable_guide") cable_guide();
  else if(part=="led_bezel") led_bezel();
  else assembly();
}
if(flat && (part=="lower_deck" || part=="upper_deck" || part=="torso_base" || part=="mast_base" || part=="head_plate" || part=="cover_front" || part=="cover_side" || part=="bumper_bar")) projection(cut=true) selected(); else selected();
