# import packages
import numpy as np
import time
import copy
# import constants
from constants import *

class Cell:
    # TODO link cell cycle to metabolic rate
    # TODO track metabolic rate as an attribute
    def __init__(self, canvas, genetics=None, cell_color=None, init_center=None):
        '''
        create a cell object that can be presented on a given center
        genetics consists of a dictionary specifying cell attributes
        '''
        # set given attributes
        self.canvas = canvas  # where we are drawing the cell
        self.cell_color = get_rand_color() if cell_color is None else cell_color
        self.genetics = {} if genetics is None else genetics  # contains all attributes
        # set constant attributes
        self.cell_radius = cell_radius  # track how big the cell is
        self.cell_health = cell_health  # food eaten - moves made
        self.cell_metabolic_cost = cell_metabolic_cost  # the rate at which movement costs energy
        self.cell_step = cell_step  # the size of the step the cell can take in any direction
        # set baseline attributes
        self.cell_alive = True  # tracks if the cell is dead
        self.cell_age = 0  # related to cell alive, after a certain age (i.e. number of rounds) the cell dies
        # create the cell
        self.instantiate(init_center)


    # define key cellular functions
    def instantiate(self, init_center=None):
        '''
        create the cell for the first time
        '''
        # create cell's position (random if not given)
        center = get_rand_coords(padding=self.cell_radius) if init_center is None else init_center
        # - specifies topleft(x,y) then bottomright(x,y)
        tl_x,tl_y,br_x,br_y = get_oval_coords(center, self.cell_radius)
        self.cell = self.canvas.create_oval(tl_x, tl_y, br_x, br_y, fill=self.cell_color, outline='maroon')
        self.cell_center = center  # track the cell center to compute movements
        # create cell's directions
        # TODO abstract this into a generalizable method via something in the constant function
        # - if needed generate random weightings
        if('cell_direction_angle' not in self.genetics):
            self.genetics['cell_direction_angle'] = get_rand_angle()
        # - if needed generate random chance of remembrance
        if('cell_cycle' not in self.genetics):
            self.genetics['cell_cycle'] = np.random.normal(loc=1, scale=0.1)  # CI=0.8-1.2
            self.genetics['cell_cycle'] = adjust_value(self.genetics['cell_cycle'], cell_cycle_llimit, cell_cycle_ulimit, continous=False)
        # - if needed generate random chance of remembrance
        if('cell_direction_remember' not in self.genetics):
            self.genetics['cell_direction_remember'] = np.random.normal(loc=0.5, scale=0.25)  # CI=0-100%
            self.genetics['cell_direction_remember'] = adjust_value(self.genetics['cell_direction_remember'], cell_direction_remember_llimit, cell_direction_remember_ulimit, continous=False)
        # get vision radius and vision nconsidered
        if('cell_vision_radius' not in self.genetics):
            self.genetics['cell_vision_radius'] = np.random.normal(loc=2, scale=0.5)  # CI=100-300% cell radius
            self.genetics['cell_vision_radius'] = adjust_value(self.genetics['cell_vision_radius'], cell_vision_radius_llimit, cell_vision_radius_ulimit, continous=False)
        if('cell_vision_nconsidered' not in self.genetics):
            self.genetics['cell_vision_nconsidered'] = np.random.normal(loc=2, scale=0.5)  # CI=1-3 foods
            self.genetics['cell_vision_nconsidered'] = adjust_value(self.genetics['cell_vision_nconsidered'], cell_vision_nconsidered_llimit, cell_vision_nconsidered_ulimit, continous=False)
        # create mutational rate
        if('cell_mutational_rate' not in self.genetics):
            self.genetics['cell_mutational_rate'] = np.random.normal(loc=cell_mutational_rate_mean, scale=cell_mutational_rate_std)  # CI=15-35% mutations <-- set in constants
            self.genetics['cell_mutational_rate'] = adjust_value(self.genetics['cell_mutational_rate'], cell_mutational_rate_llimit, cell_mutational_rate_ulimit, continous=False)
        # create mutational information
        if('cell_mutation_information' not in self.genetics):
            self.genetics['cell_mutation_information'] = []
        # we identify the keys we want to mutate
        mutational_keys = [key for key in self.genetics.keys() if key != 'cell_mutation_information']
        for key in mutational_keys:
            # > retrieve mutational percentage, also based around 25%
            mutation_perc = np.random.normal(loc=cell_mutational_rate_mean, scale=cell_mutational_rate_std)  # CI=15-35% mutations <-- set in constants
            mutation_perc = adjust_value(mutation_perc, cell_mutational_rate_llimit, cell_mutational_rate_ulimit, continous=False)
            # > retrieve mutational magnitude (dealt via special cases)
            if(key == 'cell_direction_angle'):
                mutation_magnitude = 2 * np.pi  # we want to multiply by the circle
            else:
                mutation_magnitude = 1  # we use raw percentage
            # > retrieve limits (also dealt via special cases)
            if(key == 'cell_cycle'):
                limits = cell_cycle_llimit, cell_cycle_ulimit, False
            elif(key == 'cell_direction_remember'):
                limits = cell_direction_remember_llimit, cell_direction_remember_ulimit, False
            elif(key == 'cell_vision_radius'):
                limits = cell_vision_radius_llimit, cell_vision_radius_ulimit, False
            elif(key == 'cell_vision_nconsidered'):
                limits = cell_vision_radius_llimit, cell_vision_nconsidered_ulimit, False
            elif(key == 'cell_mutational_rate'):
                limits = cell_mutational_rate_llimit, cell_mutational_rate_ulimit, False
            else:
                limits = None
            # > create and record values
            values = [key, mutation_perc, mutation_magnitude, limits]
            self.genetics['cell_mutation_information'].append(values)


    def move(self, foods):
        '''
        move the cell for a certain step
        '''
        # compute new locations
        # TODO add chance for pause
        # - get angle
        angle = self.genetics['cell_direction_angle'] if len(foods) == 0 else get_weighted_mean(foods)
        # -- we also want to set a chance for whether the cell starts following previous food path
        if(len(foods) > 0):
            record = get_spin_outcome(self.genetics['cell_direction_remember'])
            if(record):
                self.genetics['cell_direction_angle'] = angle
        # - get coordinates
        new_center = shift_coords(self.cell_center, radius=self.cell_radius, angle=angle)
        self.cell_center = new_center
        # - add step to current_location
        new_tl_x,new_tl_y,new_br_x,new_br_y = get_oval_coords(center=new_center, radius=self.cell_radius)
        # assign new coordinates
        self.canvas.coords(self.cell, new_tl_x, new_tl_y, new_br_x, new_br_y)

        # update cell attributes
        # - update cell health status
        self.cell_health -= self.cell_step * self.cell_metabolic_cost  # adjust for movement cost
        # - age the cell
        self.cell_age += 1  # as increased cell cycle means more moves per round more likekly to accrue fatal mutation
        # - check if cell needs to die
        if(self.cell_age > cell_age_of_death):
            self.cell_alive = False  # marked for apoptosis


    def eat(self, n_eaten):
        '''
        if we eat a piece of food then we revive ourselves by lowering our age
        '''
        self.cell_age -= n_eaten  # manages how long the cell may remain alive
        self.cell_health += n_eaten  # manages the cell's ability to proliferate
        # check if we need to divide
        if(self.cell_health >= cell_threshold_to_divide):
            cell = self.divide()  # cell proliferates
            return cell  # we made a new cell, let's keep track of it
        else:
            return None  # no cell to provide


    def mutate(self):
        '''
        perform mutations for the cell, for most mutations it is formatted via
        [key, mutation_perc, mutation_magnitude, (lower_limit, upper_limit)] we also deal with special cases
        '''
        # copy current genetics
        genetics = copy.deepcopy(self.genetics)
        # pull out mutational rate and information
        cell_mutational_rate = self.genetics['cell_mutational_rate']  # we want this to be unchanged during the mutation
        cell_mutation_information = genetics['cell_mutation_information']  # we want this to be changed post-mutation
        # mutate each cell
        # - key = dictionary key in genetics
        # - mutation_perc = % change to multiply by
        # - mutation_magnitude = magnitude of the change we add or subtract by
        # - limits = (lower_limit, upper_limit, continous) or None to adjust the values by
        # > rearrange the information list to put mutational rate at the front
        cell_mutation_information_front = [row for row in cell_mutation_information if row[0] == 'cell_mutational_rate']
        cell_mutation_information_rest = [row for row in cell_mutation_information if row[0] != 'cell_mutational_rate']
        cell_mutation_information = cell_mutation_information_front + cell_mutation_information_rest
        del cell_mutation_information_front, cell_mutation_information_rest
        # > process the mutations
        for idx, (key, mutation_perc, mutation_magnitude, limits) in enumerate(cell_mutation_information):
            # > mutate the attribute
            if(get_spin_outcome(cell_mutational_rate)):  # see if we need to mutate
                # compute shift
                shift = np.random.uniform(-mutation_perc, mutation_perc) * mutation_magnitude
                # perform mutation
                value = genetics[key] + shift
                # adjust values
                if(limits is not None):  # if it needs adjustment
                    lower_limit,upper_limit,continous = limits  # unpack values
                    value = adjust_value(value, lower_limit=lower_limit, upper_limit=upper_limit, continous=continous)
                # save values
                genetics[key] = value
            # > mutate the mutational rates
            # > we decide if we mutate these values based on the innate cell, but future
            #   mutational values are determined via the new mutational value as they are future cell
            if(get_spin_outcome(cell_mutational_rate)):  # see if we need to mutate
                # compute shift - currently using a fraction of the cell's mutational rate
                shift = np.random.uniform(0, 1) * genetics['cell_mutational_rate']
                # perform mutation
                value = mutation_perc + shift
                # adjust values
                value = adjust_value(value, lower_limit=0, upper_limit=1, continous=False)
                # save values (1 = index of mutational perc)
                cell_mutation_information[idx][1] = value
        # TODO correlate mutational capacity to age, and cell cycle and maybe track movement and eating separately
        # TODO mutate cell color and cell cycle
        return genetics


    def divide(self):
        '''
        divide the cell, at a random angle next to the mother cell
        '''
        # update the mother cell status
        self.cell_health -= cell_threshold_to_divide  # cost of proliferation
        # compute new locations
        # - get coordinates
        new_center= shift_coords(self.cell_center, radius=self.cell_radius)
        # create the new cell
        # - mutate the cell so the new cell can be different
        genetics = self.mutate()
        # - inherits the mutated traits of the original cell
        cell = Cell(self.canvas, genetics, cell_color=self.cell_color, init_center=new_center)
        return cell


    def die(self):
        '''
        kill the cell, leave an x and delete the original cell
        '''
        # remove the cell
        self.canvas.delete(self.cell)
