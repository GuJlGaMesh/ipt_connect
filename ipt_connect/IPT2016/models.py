from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from numpy import sort, mean
import sys

class Participant(models.Model):

	GENDER_CHOICES = ( ('M','Male'), ('F','Female'))

	ROLE_CHOICES = ( ('TM','Team Member'), ('TC','Team Captain'), ('IOC','IOC'), ('ACC','Accompanying') )

	DIET_CHOICES = ( ('NO','No specific diet'), ('NOPORK','No pork'), ('NOMEAT','No meat'), ('NOFISH','No fish'), ('NOMEAT_NOEGG','No meat, No eggs') )

	TOURISM_CHOICES = ( ('TOURISM_0','No') , ('TOURISM_1','Yes, one night'), ('TOURISM_2','Yes, two nights') )

	SHIRT_SIZES = (
		('S', 'Small'),
		('M', 'Medium'),
		('L', 'Large'),
	)

	name = models.CharField(max_length=50,default='Richard')
	surname = models.CharField(max_length=50,default='Feynman')
	gender = models.CharField(max_length=1,choices=GENDER_CHOICES)
	email = models.EmailField(help_text='This address will be used to send you every important infos about the tournament.')
	birthdate = models.DateField(default='1900-01-31')
	photo = models.ImageField(upload_to='id_photo',help_text='Used for badges and transportation cards.', blank=True, null=True)
	team = models.ForeignKey('Team')
	role = models.CharField(max_length=20,choices=ROLE_CHOICES)
	passport_number = models.CharField(max_length=20)
	affiliation = models.CharField(max_length=20,default='XXX University')
	veteran = models.BooleanField(default=False,help_text='Have you already participated in the IPT?')
	diet = models.CharField(max_length=20,choices=DIET_CHOICES,help_text='Do you have a specific diet?')
	tourism=models.CharField(max_length=20,choices=TOURISM_CHOICES,help_text='Would you like to stay some more days in Paris after the tournament? Please note the LOC would only book the rooms, not pay for it!')
	shirt_size = models.CharField(max_length=1,choices=SHIRT_SIZES)
	remark = models.TextField(blank=True)
	hotel_room = models.CharField(max_length=20,blank=True)
	check_in = models.BooleanField(default=False,help_text='Has the participant arrived?')

	# def colored_name(self):
	#     if self.name == 'Vivien':
	#         color = "green"
	#     else:
	#         color = "red"
	#     return "<span style=color:%s>%s</span>" % (color,self.name)
	# colored_name.allow_tags = True

	def fullname(self):
		return self.name+' '+self.surname

	def __str__(self):
		return self.fullname()

	def compute_average_grades(self, verbose=True):
		"""
		I collect all the grades from the Jury members that are addressed to me and compute the average grade for each fight

		:param verbose: verbosity of the function
		:return: I return a list of dictionaries, each of them with the following fields: {"value", "pf", "role"}
		"""
		#TODO: find a way to credit the points to the second reporter as well, without adding them to the total amount of team points (maybe this issue should be in the Team class ????)

		average_grades=[]

		# get all the grades that concerns me
		if verbose:
			print "="*50
			print "My name is", self.name, self.surname
		jurygrades = JuryGrade.objects.filter(physics_fight__reporter__name=self.name) | JuryGrade.objects.filter(physics_fight__opponent__name=self.name) | JuryGrade.objects.filter(physics_fight__reviewer__name=self.name)

		# get all the physics fights I'm in
		pfs = list(set([jurygrade.physics_fight for jurygrade in jurygrades]))

		if verbose:
			print "I played in %i Physics Fights" % len(pfs)

		for pf in pfs:

			# get my role in this physics fight:
			if pf.reporter.name == self.name and pf.reporter.surname == self.surname:
				role = 'reporter'
				pfgrades = list(sort([jurygrade.grade_reporter for jurygrade in jurygrades if jurygrade.physics_fight == pf]))

			elif pf.opponent.name == self.name and pf.opponent.surname == self.surname:
				role = 'opponent'
				pfgrades = list(sort([jurygrade.grade_opponent for jurygrade in jurygrades if jurygrade.physics_fight == pf]))
			elif pf.reviewer.name == self.name and pf.reviewer.surname == self.surname:
				role = 'reviewer'
				pfgrades = list(sort([jurygrade.grade_reviewer for jurygrade in jurygrades if jurygrade.physics_fight == pf]))
			else:
				print "Something wrong here...I must have a defined role !"
				sys.exit()


			if verbose:
				print "In %s, I was the %s" % (pf, role)

			# Rule for grade rejection: divide the number of jury by 4.
			# Round the result (if result is X.5, round up to X+1)
			# If the result is even, reject result/2 lowest and result/2 highest marks
			# If the result is odd, reject result/2 + 0.5 lowest and result/2 - 0.5 highest marks.
			# Example : 7 jury members --> /4 = 1.75 --> round = 2 --> reject 1 highest and 1 lowest marks

			nreject = round(len(pfgrades) / 4.0)

			if round(nreject / 2.0) == nreject / 2.0:
				nlow = int(nreject / 2.0)
				nhigh = int(nlow)
			else:
				nlow = int(nreject / 2.0 + 0.5)
				nhigh = int(nreject / 2.0 - 0.5)

			if verbose:
				print "\t%i Jury Members graded me" % len(pfgrades)
				print "\t%i lowest mark(s) and %i highest mark(s) are discarded"  % (nlow, nhigh)

			i = 0
			while i < nhigh:
				pfgrades.pop(-1)
				i += 1

			i = 0
			while i < nlow:
				pfgrades.pop(0)
				i += 1

			average_grades.append({"value": mean(pfgrades), "pf":pf, "role":role})
			if verbose:
				print '\tI scored %.2f points' % mean(pfgrades)

		return average_grades

	def points(self, verbose=True):
		"""

		:param verbose: verbosity of the function
		:return: Return the number of points gathered by a single participant. The multiplicative coefficient associated to his/her role is not taken into account here.
		"""
		points = 0.0
		average_grades = self.compute_average_grades(verbose=verbose)
		for grade in average_grades:
			points += grade["value"]
			if verbose:
				print "\tIn %s, I gathered %.2f points as a %s" % (grade["pf"], grade["value"], grade["role"])
		if verbose:
			print "In total, I gathered %.2f points" % points
		return points


	def ranking(self, pool='all', verbose=True):
		"""

		:param pool: can be "team", "gender" or "all". Select the participant you want to be ranked with
		:param verbose: verbosity of the function
		:return: return a tuple whose first element is an ordered list of participants according to the number of points they gathered, and second element is the current participant's ranking in this list
		"""


		if pool == 'team':
			participants = Participant.objects.filter(team=self.team)
		elif pool == 'gender':
			participants = Participant.objects.filter(gender=self.gender)
		elif pool == 'all':
			participants = Participant.objects.all()
		else:
			print "pool value does not compute"
			sys.exit()

		participants = sorted(participants, key=lambda x : x.points(verbose=verbose))[::-1]

		if verbose:
			print "="*20, "Ranking", "="*20
			for ind, participant in enumerate(participants):
				print ind+1,")",  participant.fullname()," - ", participant.points(verbose=False), " points"

		return participants, participants.index(self)+1



class Problem(models.Model):
	name = models.CharField(max_length=50, default=None)
	description = models.CharField(max_length=500, default=None)
	def __str__(self):

		return self.name
		
class Team(models.Model):
	name = models.CharField(max_length=50)
	surname = models.CharField(max_length=50, null=True, blank=True, default=None)
	IOC = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
	def __str__(self):

		return self.name


	def compute_teampoints(self, verbose=True):
		"""
		I get all the participants that are in my team and sum their average grades, multiplied by their roles.

		:return: Return the total number of points
		"""

		participants = Participant.objects.filter(team__name=self.name)

		if verbose:
			print "="*20, "Compute Team Points", "="*20
			print "There are %i participants in %s" % (len(participants), self.name)

		#TODO: add a verbose option here
		allpoints = 0
		for participant in participants:
			points = 0
			if verbose:
				msg='In overall, I scored '
			average_grades = participant.compute_average_grades(verbose=verbose)
			for grade in average_grades:
				if grade["role"] == "reporter":
					points += grade["value"]*3.0
					if verbose:
						msg+='%.2f*3 = %.2f points as a reporter, ' % (grade["value"], grade["value"]*3)
				elif grade["role"] == "opponent":
					points += grade["value"]*2.0
					if verbose:
						msg+='%.2f*2 = %.2f points as an opponent, ' % (grade["value"], grade["value"]*2)
				elif grade["role"] == "reviewer":
					points += grade["value"]
					if verbose:
						msg+='%.2f points as a reviewer, ' % (grade["value"])

				else:
					print "Something wrong here...my role is not defined !"
					sys.exit()

			if verbose:
				msg+='for a total of %.2f points' % points
				print msg
			allpoints += points

		if verbose:
			print "Team %s has %.2f points so far !"  % (self.name, allpoints)
		return points

	def ranking(self, verbose=True):

		teams = Team.objects.all()

		teams = sorted(teams, key=lambda x : x.compute_teampoints(verbose=verbose))[::-1]
		if verbose:
			print "="*20, "Team Ranking", "="*20
			for ind, team in enumerate(teams):
				print ind+1,")", team.name," - ", team.compute_teampoints(verbose=False), " points"

		return teams, teams.index(self)+1



class Room(models.Model):
	name = models.CharField(max_length=50)
	def __str__(self):

		return self.name

class Jury(models.Model):
	name = models.CharField(max_length=50)
	team = models.ForeignKey('Team', null=True, blank=True)
	def __str__(self):

		return self.name
		
class PhysicsFight(models.Model):

	round_number = models.IntegerField(
			choices=(((ind+1, 'Round '+str(ind+1)) for ind in range(4))),
			default=None
			)

	fight_number = models.IntegerField(
			choices=(((ind+1, 'Fight '+str(ind+1)) for ind in range(4))),
			default=None
			)

	room = models.ForeignKey(Room)

	reporter = models.ForeignKey(Participant, related_name='reporter_team_1')
	reporter_2 = models.ForeignKey(Participant, blank=True, null=True, related_name='reporter_team_2')

	opponent = models.ForeignKey(Participant, related_name='opponent_team')

	reviewer = models.ForeignKey(Participant, related_name='reviewer_team')

	problem_presented = models.ForeignKey(Problem)

	submitted_date = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return "Round %i | Fight %i | Room %s" % (self.round_number, self.fight_number, self.room.name)


class JuryGrade(models.Model):

	physics_fight = models.ForeignKey(PhysicsFight)

	jury = models.ForeignKey(Jury)

	grade_reporter = models.IntegerField(
			choices=(((ind, ind) for ind in range(10+1))),
			default=None
			)

	grade_opponent = models.IntegerField(
			choices=(((ind, ind) for ind in range(10+1))),
			default=None
			)

	grade_reviewer = models.IntegerField(
			choices=(((ind, ind) for ind in range(10+1))),
			default=None
			)

	def __str__(self):
		return "Grade of %s" % self.jury

	def info(self):
		print "=" * 36
		print "Grade of %s" % self.jury
		print self.physics_fight
		print "Reporter %s from %s : %i" % (self.physics_fight.name_reporter, self.physics_fight.reporter, self.grade_reporter)
		print "Opponent %s from %s : %i" % (self.physics_fight.name_opponent, self.physics_fight.opponent, self.grade_opponent)
		print "Reviewer %s from %s : %i" % (self.physics_fight.name_reviewer, self.physics_fight.reviewer, self.grade_reviewer)


class TacticalRejection(models.Model):

	physics_fight = models.ForeignKey(PhysicsFight)

	problem = models.ForeignKey(Problem)

	def __str__(self):
		return "Problem rejected : %s" % self.problem

class EternalRejection(models.Model):

	physics_fight = models.ForeignKey(PhysicsFight)

	problem = models.ForeignKey(Problem)

	def __str__(self):
		return "Problem rejected : %s" % self.problem

