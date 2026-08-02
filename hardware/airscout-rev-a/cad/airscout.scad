// OpenPatrol AirScout Rev A — CERN-OHL-P-2.0
// Guard-ready 380 mm X quadcopter. Engineering release; physically unvalidated.
use <../../common/cad/family_style.scad>;
$fn=64;
part="assembly"; // assembly, lower_plate, upper_plate, camera_plate, battery_tray, arm_clamp, motor_mount, landing_leg, prop_guard_segment, gps_mast, shell_top, shell_bottom
flat=false;
plate_t=2;
body_x=170;
body_y=150;
arm_square=20;
motor_diagonal=380;
motor_xy=motor_diagonal/(2*sqrt(2));
prop_d=9*25.4;
mount_hole=3.4;

module rounded_plate(x,y,t,r=14){linear_extrude(t) offset(r=r) square([x-2*r,y-2*r],center=true);}
module slot(length=18,width=4,height=6){hull(){translate([-length/2+width/2,0,0]) cylinder(h=height,d=width);translate([length/2-width/2,0,0]) cylinder(h=height,d=width);}}
module fc_pattern(h=6){for(x=[-15,15]) for(y=[-15,15]) translate([x,y,-1]) cylinder(h=h,d=3.2);}
module arm_slots(h=6){for(a=[45,135,225,315]) rotate([0,0,a]){for(y=[-12,12]) translate([72,y,-1]) slot(24,4.2,h);}}

module lower_plate(){
  difference(){
    rounded_plate(body_x,body_y,plate_t,16);
    fc_pattern(plate_t+2); arm_slots(plate_t+2);
    for(y=[-42,42]) translate([-25,y,-1]) slot(72,6,plate_t+2); // battery straps
    translate([45,0,-1]) rounded_plate(46,30,plate_t+2,6); // cable/service opening
    for(x=[-65,65]) for(y=[-55,55]) translate([x,y,-1]) cylinder(h=plate_t+2,d=4.2);
  }
}
module upper_plate(){
  difference(){
    rounded_plate(155,135,plate_t,16);
    fc_pattern(plate_t+2); arm_slots(plate_t+2);
    for(x=[-52:13:52]) translate([x,0,-1]) slot(26,3.6,plate_t+2);
    for(x=[-60,60]) for(y=[-48,48]) translate([x,y,-1]) cylinder(h=plate_t+2,d=4.2);
  }
}
module camera_plate(){
  difference(){rounded_plate(72,52,2,8);for(x=[-26,26]) translate([x,0,-1]) slot(18,3.4,4);for(y=[-18,18]) translate([0,y,-1]) cylinder(h=4,d=3.4);}
}
module battery_tray(){
  difference(){rounded_plate(145,58,2,8);for(x=[-48,48]) for(y=[-20,20]) translate([x,y,-1]) slot(20,4,4);for(y=[-18,18]) translate([0,y,-1]) slot(112,7,4);}
}
module arm_clamp(){
  difference(){
    op_round_box([46,34,22],r=5);
    cube([52,arm_square+.5,arm_square+.5],center=true);
    for(y=[-13,13]) translate([0,y,-18]) cylinder(h=36,d=4.2);
    translate([0,0,11]) cube([4,40,14],center=true);
  }
}
module motor_mount(){
  difference(){
    union(){cylinder(h=5,d=48,center=true);translate([-25,0,0]) cube([30,28,5],center=true);}
    cylinder(h=8,d=10,center=true);
    for(a=[45,135,225,315]) rotate([0,0,a]) translate([9.5,0,-5]) cylinder(h=10,d=3.4);
    for(y=[-8,8]) translate([-34,y,-5]) cylinder(h=10,d=4.2);
  }
}
module landing_leg(){
  difference(){
    hull(){translate([0,0,0]) op_round_box([24,28,12],r=4);translate([0,0,-58]) op_round_box([48,20,12],r=5);}
    translate([0,0,3]) cube([21,21,22],center=true);
    for(y=[-9,9]) translate([0,y,-10]) rotate([0,90,0]) cylinder(h=34,d=4.2,center=true);
  }
}
module prop_guard_segment(){
  // One printable quarter-ring; four per motor make a complete indoor guard.
  difference(){
    rotate_extrude(angle=92) translate([prop_d/2+13,0,0]) circle(d=8);
    translate([-400,-400,-20]) cube([400,800,40]);
  }
  translate([prop_d/2+13,0,0]) cube([34,8,8],center=true);
}
module gps_mast(){
  difference(){union(){cylinder(h=42,d1=18,d2=12);translate([0,0,42]) cylinder(h=4,d=42);}cylinder(h=50,d=4.2);}
}
module shell_top(){
  difference(){
    hull(){translate([-18,0,14]) op_round_box([118,118,46],r=16);translate([50,0,4]) op_round_box([40,82,28],r=11);}
    translate([0,0,-25]) cube([180,160,50],center=true);
    translate([-30,0,5]) cylinder(h=70,d=48);
    for(x=[-44:11:44]) translate([x,52,0]) rotate([90,0,0]) cylinder(h=8,d=4);
  }
}
module shell_bottom(){
  difference(){
    hull(){translate([-18,0,-13]) op_round_box([118,118,34],r=14);translate([50,0,-8]) op_round_box([40,82,24],r=10);}
    translate([0,0,20]) cube([180,160,50],center=true);
    translate([58,0,-18]) op_round_box([44,72,26],r=8);
  }
}
module motor(pos=[0,0,0],spin=1){
  translate(pos){
    color("#17191C") cylinder(h=32,d=29);
    color("#25282B") translate([0,0,30]) cylinder(h=5,d=38);
    color([.12,.12,.13,.65]) translate([0,0,36]) rotate([0,0,spin*8]) cube([prop_d,18,3],center=true);
  }
}
module assembly(){
  color("#4A4D52") translate([0,0,0]) lower_plate();
  color("#B8BBC0") translate([0,0,48]) upper_plate();
  for(x=[-motor_xy,motor_xy]) for(y=[-motor_xy,motor_xy]){
    a=atan2(y,x);
    color("#25282B") translate([x/2,y/2,28]) rotate([0,0,a]) cube([sqrt(x*x+y*y)-70,arm_square,arm_square],center=true);
    color("#30343A") translate([x,y,31]) motor_mount();
    motor([x,y,34],x*y>0?1:-1);
    color("#25282B") translate([x*.58,y*.58,-28]) landing_leg();
  }
  translate([0,0,46]) op_drone_shell(210,145,76);
  color("#25282B") translate([78,0,20]) camera_plate();
  translate([-28,0,82]) op_antenna(45,4);
  color("#E7E4DC") translate([-38,0,84]) gps_mast();
  color("#2F8BFF") translate([50,-60,48]) op_led_bar(22,5,2,"#2F8BFF");
}
module selected(){
  if(part=="lower_plate") lower_plate();
  else if(part=="upper_plate") upper_plate();
  else if(part=="camera_plate") camera_plate();
  else if(part=="battery_tray") battery_tray();
  else if(part=="arm_clamp") arm_clamp();
  else if(part=="motor_mount") motor_mount();
  else if(part=="landing_leg") landing_leg();
  else if(part=="prop_guard_segment") prop_guard_segment();
  else if(part=="gps_mast") gps_mast();
  else if(part=="shell_top") shell_top();
  else if(part=="shell_bottom") shell_bottom();
  else assembly();
}
if(flat && (part=="lower_plate" || part=="upper_plate" || part=="camera_plate" || part=="battery_tray")) projection(cut=true) selected(); else selected();
