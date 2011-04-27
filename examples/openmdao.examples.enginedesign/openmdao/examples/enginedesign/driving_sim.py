"""
  driving_sim.py - Driving Simulation for the vehicle example problem.

  Contains OpenMDAO drivers that can simulate different driving regimes
  for a Vehicle assembly.
  
  SimAcceleration: Determines 0-60 acceleration time
  SimEconomy: Simulates fuel economy over a velocity profile
              as used to estimate EPA city and highway mpg
"""

# pylint: disable-msg=E0611,F0401
from openmdao.lib.datatypes.api import Float
from openmdao.main.api import Driver, convert_units
from openmdao.main.hasobjective import HasObjectives
from openmdao.main.hasparameters import HasParameters
from openmdao.util.decorators import add_delegate


@add_delegate(HasObjectives, HasParameters)
class SimAcceleration(Driver):
    """ Simulation of vehicle acceleration performance. This is a specialized
    simulation driver whose workflow should consist of a Vehicle assembly, and
    whose connections are as follows:
    
    Connections
    Parameters: [ velocity (Float),
                  throttle (Float),
                  current_gear (Enum) ]
    Objectives: [ acceleration (Float), 
                  overspeed (Bool) ]
                  
    Inputs
    end_speed: float
        Ending speed for the simulation (default 60 mph)
    
    timestep: float
        Simulation time step (default .01)
        
    Outputs
    accel_time: float
        Time to perform the acceleration test.
    """

    end_speed = Float(60.0, iotype='in', units='mi/h',
                      desc='Simulation final speed')
    timestep = Float(0.1, iotype='in', units='s', 
                     desc='Simulation time step size')
    
    accel_time = Float(0.0, iotype='out', units='s',
                       desc = 'Acceleration time')
    
    def execute(self):
        """ Simulate the vehicle model at full throttle."""
        
        # Set initial throttle, gear, and velocity
        time = 0.0
        velocity = 0.0
        throttle = 1.0
        gear = 1
        
        while velocity < self.end_speed:
            
            self.set_parameters([velocity, throttle, gear])
            self.run_iteration()
            
            objs = self.eval_objectives()
            overspeed = objs[1]
            
            # If RPM goes over MAX RPM, shift gears
            # (i.e.: shift at redline)
            if overspeed:
                gear += 1
                self.set_parameters([velocity, throttle, gear])
                self.run_iteration()
                objs = self.eval_objectives()
                overspeed = objs[1]
                
                if overspeed:
                    self.raise_exception("Gearing problem in Accel test.", 
                                             RuntimeError)

            # Accleration converted to mph/s
            acceleration = convert_units(objs[0], 'm/(s*s)', 'mi/(h*s)')
            #acceleration = objs[0]*2.2369362920544025
            
            if acceleration <= 0.0:
                self.raise_exception("Vehicle could not reach maximum speed "+\
                                     "in Acceleration test.", RuntimeError)
                
            velocity += (acceleration*self.timestep)
        
            time += self.timestep
                   
        self.accel_time = time

        
@add_delegate(HasObjectives, HasParameters)
class SimEconomy(Driver):
    """ Simulation of vehicle performance over a given velocity profile. Such
    a simulation can be used to mimic the EPA city and highway driving tests.
    This is a specialized simulation driver whose workflow should consist of a
    Vehicle assembly, and whose connections are as follows:
    
    Connections
    Parameters: [ velocity (Float),
                  throttle (Float),
                  current_gear (Enum) ]
    Objectives: [ acceleration (Float), 
                  fuel burn (Float),
                  overspeed (Bool),
                  underspeed (Bool) ]
                  
    Inputs
    end_speed: float
        Ending speed for the simulation (default 60 mph)
    
    timestep: float
        Simulation time step (default .01)
        
    Outputs
    fuel_economy: float
        Fuel economy over the simulated profile.
    """

    # These can be used to adjust driving style.
    throttle_min = Float(.07, iotype='in', desc='Minimum throttle position')
    throttle_max = Float(1.0, iotype='in', desc='Maximum throttle position')
    shiftpoint1 = Float(10.0, iotype='in', \
                        desc='Always in first gear below this speed')
    
    tolerance = Float(0.01, iotype='in', 
                      desc='Convergence tolerance for Bisection solution')
    
    fuel_economy = Float(0.0, iotype='out', units='s',
                       desc = 'Simulated fuel economy over profile')
    

    def execute(self):
        """ Simulate the vehicle over a velocity profile."""
        
        # Set initial throttle, gear, and velocity
        time = 0.0
        velocity = 0.0
        throttle = 1.0
        gear = 1
       
    def _findgear(self):
        """ Finds the nearest gear in the appropriate range for the
        currently commanded vehicle state (throttle, velocity).
        
        This is intended to be called recursively.
        """

        self.run_iteration()
        
        objs = self.eval_objectives()
        overspeed = objs[2]
        underspeed = objs[3]
        
        if overspeed:
            params = self.get_parameters().values()
            gear = params[2].expreval.evaluate()
            gear += 1
            
            if gear > 4:
                self.raise_exception("Transmission gearing cannot " \
                "achieve acceleration and speed required by EPA " \
                "test.", RuntimeError)
            
        elif overspeed:
            params = self.get_parameters().values()
            gear = params[2].expreval.evaluate()
            gear -= 1
            
            # Note, no check needed for low gearing -- we allow underspeed 
            # while in first gear.
                
        else:
            return
            
        params[2] = gear
        self.set_parameters(params)
        self._findgear()        


'''
class DrivingSim(Assembly):
    """ Simulation of vehicle performance.
        
        
    def execute(self):
        """ Simulate the vehicle model at full throttle."""
        
        
        #--------------------------------------------------------------------
        # Simulate EPA driving profiles
        #--------------------------------------------------------------------
        
        profilenames = [ "EPA-city.csv", "EPA-highway.csv" ]
        
        self.vehicle.current_gear = 1
        self.vehicle.velocity = 0.0
        
        fuel_economy = []
        
                
        
        for profilename in profilenames:
            
            profile_stream = resource_stream('openmdao.examples.enginedesign',
                                             profilename)
            profile_reader = reader(profile_stream, delimiter=',')
            
            time1 = 0.0
            velocity1 = 0.0
            distance = 0.0
            fuelburn = 0.0
            
            for row in profile_reader:
                
                time2 = float(row[0])
                velocity2 = float(row[1])
                CONVERGED = 0
                
                self.vehicle.velocity = velocity1
                command_accel = (velocity2-velocity1)/(time2-time1)
                
                #------------------------------------------------------------
                # Choose the correct Gear
                #------------------------------------------------------------

                # First, if speed is less than 10 mph, put it in first gear.
                # Note: some funky gear ratios might not like this.
                # So, it's a hack for now.
                
                if velocity1 < SHIFTPOINT1:
                    self.vehicle.current_gear = 1
                    
                # Find out min and max accel in current gear.
                
                self.vehicle.throttle = THROTTLE_MIN
                findgear()                    
                accel_min = self.vehicle.acceleration*CONVERT_TO_MPHPS
                
                # Upshift if commanded accel is less than closed-throttle accel
                # The net effect of this will often be a shift to a higher gear
                # when the vehicle stops accelerating, which is reasonable.
                # Note, this isn't a While loop, because we don't want to shift
                # to 5th every time we slow down.
                if command_accel < accel_min and \
                   self.vehicle.current_gear < 5 and \
                   velocity1 > SHIFTPOINT1:
                    
                    self.vehicle.current_gear += 1
                    findgear()
                    accel_min = self.vehicle.acceleration*CONVERT_TO_MPHPS
                
                self.vehicle.throttle = THROTTLE_MAX
                self.vehicle.run()
                accel_max = self.vehicle.acceleration*CONVERT_TO_MPHPS
                
                # Downshift if commanded accel > wide-open-throttle accel
                while command_accel > accel_max and \
                      self.vehicle.current_gear > 1:
                    
                    self.vehicle.current_gear -= 1
                    findgear()
                    accel_max = self.vehicle.acceleration*CONVERT_TO_MPHPS
                
                # If engine cannot accelerate quickly enough to match profile, 
                # then raise exception    
                if command_accel > accel_max:
                    self.raise_exception("Vehicle is unable to achieve " \
                    "acceleration required to match EPA driving profile.", 
                                                    RuntimeError)
                        
                #------------------------------------------------------------
                # Bisection solution to find correct Throttle position
                #------------------------------------------------------------

                # Deceleration at closed throttle
                if command_accel < accel_min:
                    self.vehicle.throttle = THROTTLE_MIN
                    self.vehicle.run()                   
                else:
                    self.vehicle.throttle = THROTTLE_MIN
                    self.vehicle.run()
                    
                    min_acc = self.vehicle.acceleration*CONVERT_TO_MPHPS
                    max_acc = accel_max
                    min_throttle = THROTTLE_MIN
                    max_throttle = THROTTLE_MAX
                    new_throttle = .5*(min_throttle + max_throttle)
                    
                    # Numerical solution to find throttle that matches accel
                    while not CONVERGED:
                    
                        self.vehicle.throttle = new_throttle
                        self.vehicle.run()
                        new_acc = self.vehicle.acceleration*CONVERT_TO_MPHPS
                        
                        if abs(command_accel-new_acc) < MAX_ERROR:
                            CONVERGED = 1
                        else:
                            if new_acc < command_accel:
                                min_throttle = new_throttle
                                min_acc = new_acc
                                step = (command_accel-min_acc)/(max_acc-new_acc)
                                new_throttle = min_throttle + \
                                            step*(max_throttle-min_throttle)
                            else:
                                max_throttle = new_throttle
                                step = (command_accel-min_acc)/(new_acc-min_acc)
                                new_throttle = min_throttle + \
                                            step*(max_throttle-min_throttle)
                                max_acc = new_acc
                          
                distance += .5*(velocity2+velocity1)*(time2-time1)
                fuelburn += self.vehicle.fuel_burn*(time2-time1)
                
                velocity1 = velocity2
                time1 = time2
                
                #print "T = %f, V = %f, Acc = %f" % (time1, velocity1, 
                #command_accel)
                #print self.vehicle.current_gear, accel_min, accel_max
                
            # Convert liter to gallon and sec/hr to hr/hr
            distance = distance/3600.0
            fuelburn = fuelburn*(0.264172052)
            fuel_economy.append(distance/fuelburn)
            
        self.EPA_city = fuel_economy[0]
        self.EPA_highway = fuel_economy[1]
'''

if __name__ == "__main__": # pragma: no cover
    
    import time
    ttime = time.time()
    
    from openmdao.main.api import set_as_top, Assembly
    from openmdao.examples.enginedesign.vehicle import Vehicle
    
    top = set_as_top(Assembly())
    top.add('sim_acc', SimAcceleration())
    top.add('sim_EPA_city', SimEconomy())
    top.add('sim_EPA_highway', SimEconomy())
    top.add('vehicle', Vehicle())
    
    top.driver.workflow.add('sim_acc')
    top.driver.workflow.add('sim_EPA_city')
    top.driver.workflow.add('sim_EPA_highway')
    
    top.sim_acc.workflow.add('vehicle')
    top.sim_acc.add_parameters([('vehicle.velocity', 0, 99999),
                               ('vehicle.throttle', 0.01, 1.0),
                               ('vehicle.current_gear', 0, 5)])
    top.sim_acc.add_objective('vehicle.acceleration')
    top.sim_acc.add_objective('vehicle.overspeed')
    
    top.sim_EPA_city.workflow.add('vehicle')
    top.sim_EPA_city.add_parameters([('vehicle.velocity', 0, 99999),
                                     ('vehicle.throttle', 0.01, 1.0),
                                     ('vehicle.current_gear', 0, 5)])
    top.sim_EPA_city.add_objective('vehicle.acceleration')
    top.sim_EPA_city.add_objective('vehicle.fuel_burn')
    top.sim_EPA_city.add_objective('vehicle.overspeed')
    top.sim_EPA_city.add_objective('vehicle.underspeed')
    
    top.sim_EPA_highway.workflow.add('vehicle')
    top.sim_EPA_highway.add_parameters([('vehicle.velocity', 0, 99999),
                                        ('vehicle.throttle', 0.01, 1.0),
                                        ('vehicle.current_gear', 0, 5)])
    top.sim_EPA_highway.add_objective('vehicle.acceleration')
    top.sim_EPA_highway.add_objective('vehicle.fuel_burn')
    top.sim_EPA_highway.add_objective('vehicle.overspeed')
    top.sim_EPA_highway.add_objective('vehicle.underspeed')
    
    top.run()
    
    print "Time (0-60): ", top.sim_acc.accel_time
    print "City MPG: ", top.sim_EPA_city.fuel_economy
    print "Highway MPG: ", top.sim_EPA_highway.fuel_economy
    
    print "\nElapsed time: ", time.time()-ttime
    

# End driving_sim.py        
