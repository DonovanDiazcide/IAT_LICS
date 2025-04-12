import time
import random
from otree.api import *
from otree import settings
from . import stimuli
from . import blocks
from . import stats

doc = """
Implicit Association Test, draft. 
"""

#comentario random.
# estoy haciendo cambios.


class Constants(BaseConstants):
    name_in_url = 'iat'
    players_per_group = None
    num_rounds = 19

    keys = {"f": 'left', "j": 'right'}
    trial_delay = 0.250

def url_for_image(filename):
    return f"/static/images/{filename}"

class Subsession(BaseSubsession):
    practice = models.BooleanField()
    primary_left = models.StringField()
    primary_right = models.StringField()
    secondary_left = models.StringField()
    secondary_right = models.StringField()

def get_block_for_round(rnd, params):
    """Get a round setup from BLOCKS with actual categories' names substituted from session config
    The `rnd`: Player or Subsession.
    """
    block = blocks.BLOCKS[rnd]
    result = blocks.configure(block, params)
    return result

def thumbnails_for_block(block, params):
    """Return image urls for each category in block.
    Taking first image in the category as a thumbnail.
    """
    thumbnails = {'left': {}, 'right': {}}
    for side in ['left', 'right']:
        for cls in ['primary', 'secondary']:
            if cls in block[side] and params[f"{cls}_images"]:
                # use first image in categopry as a corner thumbnail
                images = stimuli.DICT[block[side][cls]]
                thumbnails[side][cls] = url_for_image(images[0])
    return thumbnails


def labels_for_block(block):
    """Return category labels for each category in block
    Just stripping prefix "something:"
    """
    labels = {'left': {}, 'right': {}}
    for side in ['left', 'right']:
        for cls in ['primary', 'secondary']:
            if cls in block[side]:
                cat = block[side][cls]
                if ':' in cat:
                    labels[side][cls] = cat.split(':')[1]
                else:
                    labels[side][cls] = cat
    return labels

def get_num_iterations_for_round(rnd):
    """Get configured number of iterations
    The `rnd`: Player or Subsession
    """
    idx = rnd.round_number
    num = rnd.session.params['num_iterations'][idx]
    return num

def creating_session(subsession: Subsession):
    session = subsession.session

    # Configuración por defecto
    defaults = dict(
        retry_delay=0.5,
        trial_delay=0.5,
        primary=[None, None],
        primary_images=False,
        secondary=[None, None],
        secondary_images=False,
        num_iterations={
            1: 5, 2: 5, 3: 10, 4: 20, 5: 5, 6: 10, 7: 20,
            8: 5, 9: 5, 10: 10, 11: 20, 12: 5, 13: 10, 14: 20,
            15: 1, 16: 1, 17: 1, 18: 1, 19: 1
        },
    )

    # Actualizar parámetros de la sesión con configuración personalizada
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])

    # Generar el orden de rondas aleatorio
    if not hasattr(session, 'order_sequence'):
        orden1 = list(range(1, 15))
        orden2 = list(range(8, 15)) + list(range(1, 8))
        rondas_15_18 = list(range(15, 19))
        random.shuffle(rondas_15_18)

        # Selección aleatoria entre orden1 y orden2
        orden_inicial_elegido = random.choice([orden1, orden2])
        orden_completo = orden_inicial_elegido + rondas_15_18 + [19]

        # Almacenar el orden en la sesión
        session.order_sequence = orden_completo

        # Imprimir el orden para depuración
        print("Orden generado:", orden_completo)

    # Usar el orden generado para la ronda actual
    orden_completo = session.order_sequence
    actual_round = orden_completo[subsession.round_number - 1]

    # Obtener el bloque correspondiente
    block = get_block_for_round(actual_round, session.params)

    # Asignar los parámetros al subsession
    subsession.practice = block['practice']
    subsession.primary_left = block['left'].get('primary', "")
    subsession.primary_right = block['right'].get('primary', "")
    subsession.secondary_left = block['left'].get('secondary', "")
    subsession.secondary_right = block['right'].get('secondary', "")

    # Imprimir la ronda actual para depuración
    print(f"Ronda actual: {subsession.round_number}, actual_round: {actual_round}")

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    iteration = models.IntegerField(initial=0)  # Contador para iteraciones del jugador
    num_trials = models.IntegerField(initial=0)  # Número total de intentos del jugador
    num_correct = models.IntegerField(initial=0)  # Número de respuestas correctas
    num_failed = models.IntegerField(initial=0)  # Número de respuestas incorrectas
    name = models.StringField(label="Nombre")
    age = models.IntegerField(label="Edad", min=0, max=99)
    sports = models.StringField(
        widget=widgets.RadioSelect,
        choices=[
            ('Football', 'Football'),
            ('Basketball', 'Basketball'),
            ('Tennis', 'Tennis'),
            ('Swimming', 'Swimming'),
            ('Other', 'Other'),
        ],
        label="¿Cuál es tu deporte favorito?"
    )
    random_number = models.IntegerField(label="Número aleatorio entre 1 y 20", min=1, max=20)

    # Nuevo campo para la pregunta moral
    moral_question = models.StringField(label="Aquí va una pregunta moral", blank=True)

    # nuevos dscores:
    dscore1 = models.FloatField()
    dscore2 = models.FloatField()

    # Nuevos campos para las etapas después del iat:

    iat1_self_assessment = models.StringField(
        label="¿Cómo crees que te fue en el IAT 1 de male y female?",
        choices=[
            "Asociación leve a male+feliz, female+triste",
            "Asociación leve a male+triste, female+feliz",
            "Asociación moderada a male+feliz, female+triste",
            "Asociación moderada a male+triste, female+feliz",
            "Asociación fuerte a male+feliz, female+triste",
            "Asociación fuerte a male+triste, female+feliz",
        ],
        widget=widgets.RadioSelect
    )

    # Respuesta de autoevaluación para el IAT 2 (Ejemplo: Gato y Perro)
    iat2_self_assessment = models.StringField(
        label="¿Cómo crees que te fue en el IAT 2 de gato y perro?",
        choices=[
            "Asociación leve a gato+feliz, perro+triste",
            "Asociación leve a gato+triste, perro+feliz",
            "Asociación moderada a gato+feliz, perro+triste",
            "Asociación moderada a gato+triste, perro+feliz",
            "Asociación fuerte a gato+feliz, perro+triste",
            "Asociación fuerte a gato+triste, perro+feliz",
        ],
        widget=widgets.RadioSelect
    )

    # Variables para el rango moralmente aceptable del IAT 1
    iat1_lower_limit = models.FloatField(
        label="¿Cuál es el límite inferior del rango moralmente aceptable para el IAT 1?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    iat1_upper_limit = models.FloatField(
        label="¿Cuál es el límite superior del rango moralmente aceptable para el IAT 1?",
        help_text="Debe estar entre -2 y 2. (deber ser mayor el límite inferior)",
        min=-2,
        max=2
    )

    # Variables para el rango moralmente aceptable del IAT 2
    iat2_lower_limit = models.FloatField(
        label="¿Cuál es el límite inferior del rango moralmente aceptable para el IAT 2?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    iat2_upper_limit = models.FloatField(
        label="¿Cuál es el límite superior del rango moralmente aceptable para el IAT 2?",
        help_text="Debe estar entre -2 y 2. (deber ser mayor el límite inferior)",
        min=-2,
        max=2
    )

    hide_iat1_info_in_range = models.BooleanField(
        label="¿Quieres que se esconda la información del IAT 1 para decisiones morales si está dentro de tu rango moralmente aceptable?",
        choices=[
            (True, "Sí"),
            (False, "No")
        ]
    )
    hide_iat1_info_out_of_range = models.BooleanField(
        label="¿Quieres que se esconda la información del IAT 1 para decisiones morales si está fuera de tu rango moralmente aceptable?",
        choices=[
            (True, "Sí"),
            (False, "No")
        ]
    )

    # Campos para ocultar información del IAT 2
    hide_iat2_info_in_range = models.BooleanField(
        label="¿Quieres que se esconda la información del IAT 2 para decisiones morales si está dentro de tu rango moralmente aceptable?",
        choices=[
            (True, "Sí"),
            (False, "No")
        ]
    )
    hide_iat2_info_out_of_range = models.BooleanField(
        label="¿Quieres que se esconda la información del IAT 2 para decisiones morales si está fuera de tu rango moralmente aceptable?",
        choices=[
            (True, "Sí"),
            (False, "No")
        ]
    )

    # variables para el juego del dictador:

    # Variables de dinero inicial para cada caso
    dinero_inicial_cats = models.FloatField(initial=100.0)
    dinero_inicial_dogs = models.FloatField(initial=100.0)
    dinero_inicial_white = models.FloatField(initial=100.0)
    dinero_inicial_black = models.FloatField(initial=100.0)

    asignacion_cats = models.FloatField(
        min=0.0,
        max=100.0,
        label="¿Cuánto quieres donar a una asociación para gatos callejeros?",
        help_text="no puedes dar cantidades negativas ni pasarte de tu asignación inicial"
    )
    asignacion_dogs = models.FloatField(
        min=0.0,
        max=100.0,
        label="¿Cuánto quieres donar a una asociación para perros callejeros?",
        help_text="no puedes dar cantidades negativas ni pasarte de tu asignación inicial"
    )
    asignacion_white = models.FloatField(
        min=0.0,
        max=100.0,
        label="¿Cuánto quieres donar a una asociación para personas blancas?",
        help_text="no puedes dar cantidades negativas ni pasarte de tu asignación inicial"

    )
    asignacion_black = models.FloatField(
        min=0.0,
        max=100.0,
        label="¿Cuánto quieres donar a una asociación para personas negras?",
        help_text="no puedes dar cantidades negativas ni pasarte de tu asignación inicial"
    )

class Trial(ExtraModel):
    """A record of single iteration
    Keeps corner categories from round setup to simplify furher analysis.
    The stimulus class is for appropriate styling on page.
    """
    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)

    stimulus_cls = models.StringField(choices=('primary', 'secondary'))
    stimulus_cat = models.StringField()
    stimulus = models.StringField()
    correct = models.StringField(choices=('left', 'right'))

    response = models.StringField(choices=('left', 'right'))
    response_timestamp = models.FloatField()
    reaction_time = models.FloatField()
    is_correct = models.BooleanField()
    retries = models.IntegerField(initial=0)


def generate_trial(player: Player) -> Trial:
    """Create new question for a player"""
    block = get_block_for_round(player.round_number, player.session.params)
    chosen_side = random.choice(['left', 'right'])
    chosen_cls = random.choice(list(block[chosen_side].keys()))
    chosen_cat = block[chosen_side][chosen_cls]
    stimulus = random.choice(stimuli.DICT[chosen_cat])

    player.iteration += 1
    return Trial.create(
        player=player,
        iteration=player.iteration,
        timestamp=time.time(),
        #
        stimulus_cls=chosen_cls,
        stimulus_cat=chosen_cat,
        stimulus=stimulus,
        correct=chosen_side,
    )


def get_current_trial(player: Player):
    """Get last (current) question for a player"""
    trials = Trial.filter(player=player, iteration=player.iteration)
    if trials:
        [trial] = trials
        return trial

def encode_trial(trial: Trial):
    return dict(
        cls=trial.stimulus_cls,
        cat=trial.stimulus_cat,
        stimulus=url_for_image(trial.stimulus) if trial.stimulus.endswith((".png", ".jpg")) else str(trial.stimulus),
    )


def get_progress(player: Player):
    """Return current player progress"""
    return dict(
        num_trials=player.num_trials,
        num_correct=player.num_correct,
        num_incorrect=player.num_failed,
        iteration=player.iteration,
        total=get_num_iterations_for_round(player),
    )


def custom_export(players):
    """Dumps all the trials generated"""
    yield [
        "session",
        "participant_code",
        "round",
        "primary_left",
        "primary_right",
        "secondary_left",
        "secondary_right",
        "iteration",
        "timestamp",
        "stimulus_class",
        "stimulus_category",
        "stimulus",
        "expected",
        "response",
        "is_correct",
        "reaction_time",
    ]
    for p in players:
        if p.round_number not in (3, 4, 6, 7, 10, 11, 13, 14, 15, 16, 17, 18):
            continue
        participant = p.participant
        session = p.session
        subsession = p.subsession
        for z in Trial.filter(player=p):
            yield [
                session.code,
                participant.code,
                subsession.round_number,
                subsession.primary_left,
                subsession.primary_right,
                subsession.secondary_left,
                subsession.secondary_right,
                z.iteration,
                z.timestamp,
                z.stimulus_cls,
                z.stimulus_cat,
                z.stimulus,
                z.correct,
                z.response,
                z.is_correct,
                z.reaction_time,
            ]


def play_game(player: Player, message: dict):
    """Main game workflow
    Implemented as reactive scheme: receive message from vrowser, react, respond.

    Generic game workflow, from server point of view:
    - receive: {'type': 'load'} -- empty message means page loaded
    - check if it's game start or page refresh midgame
    - respond: {'type': 'status', 'progress': ...}
    - respond: {'type': 'status', 'progress': ..., 'trial': data} -- in case of midgame page reload

    - receive: {'type': 'next'} -- request for a next/first trial
    - generate new trial
    - respond: {'type': 'trial', 'trial': data}

    - receive: {'type': 'answer', 'answer': ...} -- user answered the trial
    - check if the answer is correct
    - respond: {'type': 'feedback', 'is_correct': true|false} -- feedback to the answer

    When done solving, client should explicitely request next trial by sending 'next' message

    Field 'progress' is added to all server responses to indicate it on page.

    To indicate max_iteration exhausted in response to 'next' server returns 'status' message with iterations_left=0
    """
    session = player.session
    my_id = player.id_in_group
    ret_params = session.params
    max_iters = get_num_iterations_for_round(player)

    now = time.time()
    # the current trial or none
    current = get_current_trial(player)

    message_type = message['type']

    # print("iteration:", player.iteration)
    # print("current:", current)
    # print("received:", message)

    # page loaded
    if message_type == 'load':
        p = get_progress(player)
        if current:
            return {my_id: dict(type='status', progress=p, trial=encode_trial(current))}
        else:
            return {my_id: dict(type='status', progress=p)}

    # client requested new trial
    if message_type == "next":
        if current is not None:
            if current.response is None:
                raise RuntimeError("trying to skip over unsolved trial")
            if now < current.timestamp + ret_params["trial_delay"]:
                raise RuntimeError("retrying too fast")
            if current.iteration == max_iters:
                return {
                    my_id: dict(
                        type='status', progress=get_progress(player), iterations_left=0
                    )
                }
        # generate new trial
        z = generate_trial(player)
        p = get_progress(player)
        return {my_id: dict(type='trial', trial=encode_trial(z), progress=p)}

    # client gives an answer to current trial
    if message_type == "answer":
        if current is None:
            raise RuntimeError("trying to answer no trial")

        if current.response is not None:  # it's a retry
            if now < current.response_timestamp + ret_params["retry_delay"]:
                raise RuntimeError("retrying too fast")

            # undo last updation of player progress
            player.num_trials -= 1
            if current.is_correct:
                player.num_correct -= 1
            else:
                player.num_failed -= 1

        # check answer
        answer = message["answer"]

        if answer == "" or answer is None:
            raise ValueError("bogus answer")

        current.response = answer
        current.reaction_time = message["reaction_time"]
        current.is_correct = current.correct == answer
        current.response_timestamp = now

        # update player progress
        if current.is_correct:
            player.num_correct += 1
        else:
            player.num_failed += 1
        player.num_trials += 1

        p = get_progress(player)
        return {
            my_id: dict(
                type='feedback',
                is_correct=current.is_correct,
                progress=p,
            )
        }

    if message_type == "cheat" and settings.DEBUG:
        # generate remaining data for the round
        m = float(message['reaction'])
        if current:
            current.delete()
        for i in range(player.iteration, max_iters):
            t = generate_trial(player)
            t.iteration = i
            t.timestamp = now + i
            t.response = t.correct
            t.is_correct = True
            t.response_timestamp = now + i
            t.reaction_time = random.gauss(m, 0.3)
        return {
            my_id: dict(type='status', progress=get_progress(player), iterations_left=0)
        }
    raise RuntimeError("unrecognized message from client")

# PAGES. cambiecito.
class Intro(Page):
    @staticmethod
    def is_displayed(player):
        # Display the page in rounds 1 and 8
        return player.round_number in [1, 8]

    @staticmethod
    def vars_for_template(player: Player):
        # Determine the block based on the round number
        params = player.session.params
        if player.round_number == 1:
            block = get_block_for_round(3, params)  # Use block for round 3 in round 1
        elif player.round_number == 8:
            block = get_block_for_round(10, params)  # Use block for round 10 in round 8
        else:
            block = None  # Fallback in case of unexpected behavior

        return dict(
            params=params,
            labels=labels_for_block(block) if block else {},
        )



class UserInfo(Page):
    form_model = 'player'
    form_fields = ['name', 'age', 'sports', 'random_number']

    @staticmethod
    def is_displayed(player):
        # Mostrar esta página solo una vez por participante
        return player.participant.vars.get('user_info_completed', False) == False

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Establecer valores predeterminados si están vacíos
        participant = player.participant
        if not player.name:
            player.name = "Anónimo"
        if not player.age:
            player.age = 18
        if not player.sports:
            player.sports = "Sin especificar"
        if not player.random_number:
            player.random_number = 0

        # Marcar que la información ya fue recopilada
        participant.vars['user_info_completed'] = True


class PreguntaM(Page):
    form_model = 'player'
    form_fields = ['moral_question']

    @staticmethod
    def is_displayed(player):
        # Mostrar esta página solo una vez por participante
        return player.participant.vars.get('pregunta_moral_completada', False) == False

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Marcar que la página ya fue completada
        player.participant.vars['pregunta_moral_completada'] = True

    @staticmethod
    def error_message(player, values):
        # Validar que el campo moral_question no esté vacío
        if not values.get('moral_question'):
            return "Por favor, responde la pregunta antes de continuar."

class RoundN(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def is_displayed(player: Player):
        # Mostrar solo en rondas de IAT
        return player.round_number <= 14

    @staticmethod
    def js_vars(player: Player):
        return dict(params=player.session.params, keys=Constants.keys)

    @staticmethod
    def vars_for_template(player: Player):
        params = player.session.params
        block = get_block_for_round(player.round_number, params)
        return dict(
            params=params,
            block=block,
            thumbnails=thumbnails_for_block(block, params),
            labels=labels_for_block(block),
            num_iterations=get_num_iterations_for_round(player),
            DEBUG=settings.DEBUG,
            keys=Constants.keys,
            lkeys="/".join(
                [k for k in Constants.keys.keys() if Constants.keys[k] == 'left']
            ),
            rkeys="/".join(
                [k for k in Constants.keys.keys() if Constants.keys[k] == 'right']
            ),
        )

    live_method = play_game

class FeedbackIAT(Page):
    form_model = 'player'
    form_fields = [
        'iat1_self_assessment',
        'iat2_self_assessment',
        'iat1_lower_limit',  # Límite inferior para el IAT 1
        'iat1_upper_limit',  # Límite superior para el IAT 1
        'iat2_lower_limit',  # Límite inferior para el IAT 2
        'iat2_upper_limit',  # Límite superior para el IAT 2
        'hide_iat1_info_in_range',  # Respuesta para IAT 1 dentro del rango
        'hide_iat1_info_out_of_range',  # Respuesta para IAT 1 fuera del rango
        'hide_iat2_info_in_range',  # Respuesta para IAT 2 dentro del rango
        'hide_iat2_info_out_of_range'  # Respuesta para IAT 2 fuera del rango
    ]

    @staticmethod
    def is_displayed(player):
        # Mostrar esta página solo en la ronda 15
        return player.round_number == 15

    @staticmethod
    def vars_for_template(player: Player):
        return {}

    @staticmethod
    def error_message(player, values):
        errors = {}

        # Validar límites de IAT 1
        if values['iat1_lower_limit'] >= values['iat1_upper_limit']:
            errors['iat1_upper_limit'] = "El límite superior debe ser mayor al límite inferior para el IAT 1."

        # Validar límites de IAT 2
        if values['iat2_lower_limit'] >= values['iat2_upper_limit']:
            errors['iat2_upper_limit'] = "El límite superior debe ser mayor al límite inferior para el IAT 2."

        # Retornar errores si los hay
        if errors:
            return errors

class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 15

    @staticmethod
    def vars_for_template(player: Player):
        def extract(rnd):
            trials = [
                t
                for t in Trial.filter(player=player.in_round(rnd))
                if t.reaction_time is not None
            ]
            values = [t.reaction_time for t in trials]
            return values

        # primer iat:

        # Extraer datos de las rondas para calcular el d-score
        data3 = extract(3)
        data4 = extract(4)
        data6 = extract(6)
        data7 = extract(7)

        dscore_iat1 = stats.dscore(data3, data4, data6, data7)

        # Obtener combinaciones de pares positivos y negativos para el primer IAT
        pos_pairs_iat1 = labels_for_block(get_block_for_round(3, player.session.params))
        neg_pairs_iat1 = labels_for_block(get_block_for_round(6, player.session.params))

        # Obtener combinaciones de pares positivos y negativos para el segundo IAT
        pos_pairs_iat2 = labels_for_block(get_block_for_round(10, player.session.params))
        neg_pairs_iat2 = labels_for_block(get_block_for_round(13, player.session.params))

        # segundo iat:

        # Extraer datos de las rondas para calcular el d-score
        data10 = extract(10)
        data11 = extract(11)
        data13 = extract(13)
        data14 = extract(14)

        dscore_iat2 = stats.dscore(data10, data11, data13, data14)

        # Guardar resultados en el jugador
        player.dscore1 = dscore_iat1
        player.dscore2 = dscore_iat2

        # Manejar valores del jugador
        player_name = player.field_maybe_none('name') or "Anónimo"
        player_age = player.field_maybe_none('age') or 18
        player_sports = player.field_maybe_none('sports') or "Sin especificar"
        player_random_number = player.field_maybe_none('random_number') or 0

        # Validar si los resultados están dentro o fuera de los rangos definidos
        dscore1_in_range = (
                player.dscore1 >= player.iat1_lower_limit and
                player.dscore1 <= player.iat1_upper_limit
        )
        dscore2_in_range = (
                player.dscore2 >= player.iat2_lower_limit and
                player.dscore2 <= player.iat2_upper_limit
        )

        # Decidir si mostrar u ocultar resultados en base a las preferencias del usuario
        show_dscore1 = (
                (dscore1_in_range and not player.hide_iat1_info_in_range) or
                (not dscore1_in_range and not player.hide_iat1_info_out_of_range)
        )
        show_dscore2 = (
                (dscore2_in_range and not player.hide_iat2_info_in_range) or
                (not dscore2_in_range and not player.hide_iat2_info_out_of_range)
        )

        # Mensajes según las decisiones
        message_dscore1 = "Decidiste que se mostraran los resultados para el IAT 1." if show_dscore1 else "Decidiste que no se mostrarán los resultados para el IAT 1."
        message_dscore2 = "Decidiste que se mostraran los resultados para el IAT 2." if show_dscore2 else "Decidiste que no se mostrarán los resultados para el IAT 2."

        return dict(
            show_dscore1 = show_dscore1,
            show_dscore2 = show_dscore2,
            dscore1=dscore_iat1 if show_dscore1 else None,
            dscore2=dscore_iat2 if show_dscore2 else None,
            message_dscore1 = message_dscore1,
            message_dscore2 = message_dscore2,
            pos_pairs_iat1=pos_pairs_iat1,
            neg_pairs_iat1=neg_pairs_iat1,
            pos_pairs_iat2=pos_pairs_iat2,
            neg_pairs_iat2=neg_pairs_iat2,
            player_name=player_name,
            player_age=player_age,
            player_sports=player_sports,
            player_random_number=player_random_number,
        )

class AsignacionDinero(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return 15 <= player.round_number <= 18

    @staticmethod
    def get_form_fields(player):
        """Determina qué campo de asignación mostrar según la ronda."""
        if player.round_number == 15:
            return ['asignacion_cats']
        elif player.round_number == 16:
            return ['asignacion_dogs']
        elif player.round_number == 17:
            return ['asignacion_white']
        elif player.round_number == 18:
            return ['asignacion_black']
        return []

    @staticmethod
    def vars_for_template(player: Player):
        """Proporciona variables adicionales para la plantilla."""
        if player.round_number == 15:
            contexto = {
                'inicial': player.dinero_inicial_cats,
                'beneficiario': 'una asociación sin fines de lucro para gatos callejeros'
            }
        elif player.round_number == 16:
            contexto = {
                'inicial': player.dinero_inicial_dogs,
                'beneficiario': 'una asociación sin fines de lucro para perros callejeros'
            }
        elif player.round_number == 17:
            contexto = {
                'inicial': player.dinero_inicial_white,
                'beneficiario': 'una asociación sin fines de lucro para personas blancas'
            }
        elif player.round_number == 18:
            contexto = {
                'inicial': player.dinero_inicial_black,
                'beneficiario': 'una asociación sin fines de lucro para personas negras'
            }
        else:
            contexto = {}
        return contexto

    @staticmethod
    def error_message(player, values):
        """Valida que la asignación no exceda el dinero inicial."""
        if player.round_number == 15:
            asignacion = values.get('asignacion_cats')
            inicial = player.dinero_inicial_cats
            if asignacion > inicial:
                return 'La asignación no puede exceder los 100 créditos.'
        elif player.round_number == 16:
            asignacion = values.get('asignacion_dogs')
            inicial = player.dinero_inicial_dogs
            if asignacion > inicial:
                return 'La asignación no puede exceder los 100 créditos.'
        elif player.round_number == 17:
            asignacion = values.get('asignacion_white')
            inicial = player.dinero_inicial_white
            if asignacion > inicial:
                return 'La asignación no puede exceder los 100 créditos.'
        elif player.round_number == 18:
            asignacion = values.get('asignacion_black')
            inicial = player.dinero_inicial_black
            if asignacion > inicial:
                return 'La asignación no puede exceder los 100 créditos.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Marcar que la página ya fue completada
        player.participant.vars['asignacionesDinero_completada'] = True




page_sequence = [Intro, UserInfo, PreguntaM, RoundN, FeedbackIAT, Results, AsignacionDinero]
