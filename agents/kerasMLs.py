import agents

import os
import numpy as np
from sklearn import preprocessing
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


class kerasActorCritic(agents.LogicModule):

    def __init__(self
                 , learnerDir
                 , numberOfInputs
                 , numberOfActions
                 , gamma=0.99
                 , hiddenLayers=128):
        """Based on this example: https://keras.io/examples/rl/actor_critic_cartpole/"""
        super().__init__()

        self.CoreDir = learnerDir
        self.ModelsDir = self.CoreDir + 'models/'
        self.ModelPath = self.ModelsDir + 'model'

        # Configuration parameters for the whole setup
        self.gamma = gamma  # Discount factor for past rewards
        self.eps = np.finfo(np.float32).eps.item()  # Smallest number such that 1.0 + eps != 1.0

        self.num_inputs = numberOfInputs
        self.num_actions = numberOfActions
        self.num_hidden = hiddenLayers

        self.CurrentStep = 0
        self.max_steps_per_episode = 1

        # Ensure the path exists
        os.makedirs(self.ModelsDir, exist_ok=True)

        if os.path.exists(self.ModelPath):
            self.model = keras.models.load_model(self.ModelPath)
            print('Agent: Loading existing model')
        else:

            self.inputs = layers.Input(shape=(self.num_inputs,))
            self.common = layers.Dense(self.num_hidden, activation="relu")(self.inputs)
            self.action = layers.Dense(self.num_actions, activation="softmax")(self.common)
            self.critic = layers.Dense(1)(self.common)

            self.model = keras.Model(inputs=self.inputs, outputs=[self.action, self.critic])

        # Post Model
        self.optimizer = keras.optimizers.Adam(learning_rate=0.01)
        self.huber_loss = keras.losses.Huber()
        self.action_probs_history = []
        self.critic_value_history = []
        self.rewards_history = []
        self.running_reward = 0
        self.episode_count = 0

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info):

        episode_reward = 0

        with tf.GradientTape() as tape:
            # normalize the values

            state = tf.convert_to_tensor(observation)
            state = tf.expand_dims(state, 0)

            state = preprocessing.normalize(X=state, norm='l2', axis=1)

            # Predict action probabilities and estimated future rewards
            # from environment state
            action_probs, critic_value = self.model(state)
            original_action_probs = np.squeeze(action_probs)
            self.critic_value_history.append(critic_value[0, 0])

            # SUBSET SELECTION
            # If a "subset" of actions is desired, the filtering and recalibration of the probabilities from the model is done here

            if actionSpaceSubset is not None:
                probs = np.squeeze(action_probs)
                redisprobs = []

                probSum = 0

                # filter the probs for non-allowed actions out
                for idx, prob in enumerate(probs):
                    if idx in actionSpaceSubset:
                        redisprobs.append(prob)
                        probSum += prob
                    else:
                        redisprobs.append(0)

                # adjust the probs that remain with the new total
                for idx, prob in enumerate(redisprobs):
                    redisprobs[idx] = prob / probSum

                print('action probs')
                print(action_probs)
                action_probs = tf.convert_to_tensor([redisprobs], dtype=tf.float32)

            # ================

            # Sample action from action probability distribution
            action = np.random.choice(self.num_actions, p=np.squeeze(action_probs))

            print('State {} - ActionSpace {} - ActionSpace Probs {} - Original {} - ActionSpace Subset {} - Action {}'.format(state, actionSpace, np.squeeze(action_probs), original_action_probs, actionSpaceSubset, action))

            self.action_probs_history.append(tf.math.log(action_probs[0, action]))

            # Apply the sampled action in our environment
            self.rewards_history.append(reward)
            episode_reward += reward

            if self.CurrentStep % self.max_steps_per_episode == 0:

                # Update running reward to check condition for solving
                self.running_reward = 0.05 * episode_reward + (1 - 0.05) * self.running_reward

                # Calculate expected value from rewards
                # - At each timestep what was the total reward received after that timestep
                # - Rewards in the past are discounted by multiplying them with gamma
                # - These are the labels for our critic
                returns = []
                discounted_sum = 0
                for r in self.rewards_history[::-1]:
                    discounted_sum = r + self.gamma * discounted_sum
                    returns.insert(0, discounted_sum)

                # Normalize
                returns = np.array(returns)
                returns = (returns - np.mean(returns)) / (np.std(returns) + self.eps)
                returns = returns.tolist()

                # Calculating loss values to update our network
                history = zip(self.action_probs_history, self.critic_value_history, returns)
                actor_losses = []
                critic_losses = []
                for log_prob, value, ret in history:
                    # At this point in history, the critic estimated that we would get a
                    # total reward = `value` in the future. We took an action with log probability
                    # of `log_prob` and ended up recieving a total reward = `ret`.
                    # The actor must be updated so that it predicts an action that leads to
                    # high rewards (compared to critic's estimate) with high probability.
                    diff = ret - value
                    actor_losses.append(-log_prob * diff)  # actor loss

                    # The critic must be updated so that it predicts a better estimate of
                    # the future rewards.
                    critic_losses.append(
                        self.huber_loss(tf.expand_dims(value, 0), tf.expand_dims(ret, 0))
                    )

                # Backpropagation
                loss_value = sum(actor_losses) + sum(critic_losses)
                grads = tape.gradient(loss_value, self.model.trainable_variables)
                self.optimizer.apply_gradients(zip(grads, self.model.trainable_variables))

                # Clear the loss and reward history
                self.action_probs_history.clear()
                self.critic_value_history.clear()
                self.rewards_history.clear()

                # Log details
                self.episode_count += 1
                if self.episode_count % 10 == 0:
                    template = "running reward: {:.2f} at episode {}"
                    print(template.format(self.running_reward, self.episode_count))

                if self.running_reward > 195:  # Condition to consider the task solved
                    print("Solved at episode {}!".format(self.episode_count))

                self.model.save(self.ModelPath)

        return action


class kerasDDPG(agents.LogicModule):

    def __init__(self
                 , learnerDir
                 , numberOfInputs
                 , numberOfActions
                 , gamma=0.99
                 , tau=0.005
                 , std=0.2
                 , criticLearningRate=0.002
                 , actorLearningRate=0.001
                 , experienceBufferCapacity=50000
                 , experienceBufferBatchSize=64):
        """Based on this example: https://keras.io/examples/rl/ddpg_pendulum/"""
        super().__init__()

        self.CoreDir = learnerDir
        self.ModelsDir = self.CoreDir + 'models/'
        self.ModelPath = self.ModelsDir + 'model'

        # Configuration parameters for the whole setup
        self.gamma = gamma  # Discount factor for past rewards
        self.tau = tau
        self.eps = np.finfo(np.float32).eps.item()  # Smallest number such that 1.0 + eps != 1.0

        self.num_inputs = numberOfInputs
        self.num_actions = numberOfActions

        self.CurrentStep = 0
        self.max_steps_per_episode = 1

        # Ensure the path exists
        os.makedirs(self.ModelsDir, exist_ok=True)

        if os.path.exists(self.ModelPath):
            self.model = keras.models.load_model(self.ModelPath)
            print('Loading existing model')
        else:

            # Initialize weights between -3e-3 and 3-e3
            last_init = tf.random_uniform_initializer(minval=-0.003, maxval=0.003)

            inputs = layers.Input(shape=(self.num_inputs,))
            out = layers.Dense(256, activation="relu")(inputs)
            out = layers.Dense(256, activation="relu")(out)
            outputs = layers.Dense(1, activation="tanh", kernel_initializer=last_init)(out)

            self.actor_model = tf.keras.Model(inputs, outputs)

            # State as input
            state_input = layers.Input(shape=(self.num_inputs,))
            state_out = layers.Dense(16, activation="relu")(state_input)
            state_out = layers.Dense(32, activation="relu")(state_out)

            # Action as input
            action_input = layers.Input(shape=(self.num_actions,))
            action_out = layers.Dense(32, activation="relu")(action_input)

            # Both are passed through seperate layer before concatenating
            concat = layers.Concatenate()([state_out, action_out])

            out = layers.Dense(256, activation="relu")(concat)
            out = layers.Dense(256, activation="relu")(out)
            outputs = layers.Dense(1)(out)

            # Outputs single value for give state-action
            self.critic_model = tf.keras.Model([state_input, action_input], outputs)

            last_init = tf.random_uniform_initializer(minval=-0.003, maxval=0.003)

            inputs = layers.Input(shape=(self.num_inputs,))
            out = layers.Dense(256, activation="relu")(inputs)
            out = layers.Dense(256, activation="relu")(out)
            outputs = layers.Dense(1, activation="tanh", kernel_initializer=last_init)(out)

            self.target_actor = tf.keras.Model(inputs, outputs)

            # State as input
            state_input = layers.Input(shape=(self.num_inputs,))
            state_out = layers.Dense(16, activation="relu")(state_input)
            state_out = layers.Dense(32, activation="relu")(state_out)

            # Action as input
            action_input = layers.Input(shape=(self.num_actions,))
            action_out = layers.Dense(32, activation="relu")(action_input)

            # Both are passed through seperate layer before concatenating
            concat = layers.Concatenate()([state_out, action_out])

            out = layers.Dense(256, activation="relu")(concat)
            out = layers.Dense(256, activation="relu")(out)
            outputs = layers.Dense(1)(out)

            self.target_critic = tf.keras.Model([state_input, action_input], outputs)

            # Making the weights equal initially
            self.target_actor.set_weights(self.actor_model.get_weights())
            self.target_critic.set_weights(self.critic_model.get_weights())

            self.critic_optimizer = tf.keras.optimizers.Adam(criticLearningRate)
            self.actor_optimizer = tf.keras.optimizers.Adam(actorLearningRate)

        self.Buffer = Buffer(num_states=numberOfInputs, num_actions=numberOfActions, buffer_capacity=experienceBufferCapacity, batch_size=experienceBufferBatchSize)
        self.ou_noise = OUActionNoise(mean=np.zeros(1), std_deviation=float(std) * np.ones(1))
        self.prev_state = None
        self.episodic_reward = 0

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info):

        if self.prev_state is None:
            self.prev_state = observation

        print('Obv {} Rew {}'.format(observation, reward))

        tf_prev_state = tf.expand_dims(tf.convert_to_tensor(list(self.prev_state.values())), 0)

        print('TF Prev State {}'.format(tf_prev_state))

        sampled_actions = tf.squeeze(self.actor_model(tf_prev_state))
        noise = self.ou_noise()
        # Adding noise to action
        sampled_actions = sampled_actions.numpy() + noise

        # We make sure action is within bounds
        #legal_action = np.clip(sampled_actions, lower_bound, upper_bound)

        print('Keras - DDPG - sampled actions: {}'.format(sampled_actions))

        action = 0

        self.Buffer.record((list(self.prev_state.values()), action, reward, list(observation.values())))
        self.episodic_reward += reward

        self.Buffer.learn(actor_model=self.actor_model, actor_optimizer=self.actor_optimizer, gamma=self.gamma
                          , critic_model=self.critic_model, critic_optimizer=self.critic_optimizer, target_critic=self.target_critic, target_actor=self.target_actor)
        update_target(self.target_actor.variables, self.actor_model.variables, self.tau)
        update_target(self.target_critic.variables, self.critic_model.variables, self.tau)

        self.model.save(self.ModelPath)

        return action


class OUActionNoise:
    def __init__(self, mean, std_deviation, theta=0.15, dt=1e-2, x_initial=None):
        """Ornstein-Uhlenbeck process as written by Keras : https://keras.io/examples/rl/ddpg_pendulum/"""
        self.theta = theta
        self.mean = mean
        self.std_dev = std_deviation
        self.dt = dt
        self.x_initial = x_initial
        self.reset()

    def __call__(self):
        # Formula taken from https://www.wikipedia.org/wiki/Ornstein-Uhlenbeck_process.
        x = (
            self.x_prev
            + self.theta * (self.mean - self.x_prev) * self.dt
            + self.std_dev * np.sqrt(self.dt) * np.random.normal(size=self.mean.shape)
        )
        # Store x into x_prev
        # Makes next noise dependent on current one
        self.x_prev = x
        return x

    def reset(self):
        if self.x_initial is not None:
            self.x_prev = self.x_initial
        else:
            self.x_prev = np.zeros_like(self.mean)


class Buffer:
    def __init__(self, num_states, num_actions, buffer_capacity=100000, batch_size=64):
        # Number of "experiences" to store at max
        self.buffer_capacity = buffer_capacity
        # Num of tuples to train on.
        self.batch_size = batch_size

        # Its tells us num of times record() was called.
        self.buffer_counter = 0

        # Instead of list of tuples as the exp.replay concept go
        # We use different np.arrays for each tuple element
        self.state_buffer = np.zeros((self.buffer_capacity, num_states))
        self.action_buffer = np.zeros((self.buffer_capacity, num_actions))
        self.reward_buffer = np.zeros((self.buffer_capacity, 1))
        self.next_state_buffer = np.zeros((self.buffer_capacity, num_states))

    # Takes (s,a,r,s') obervation tuple as input
    def record(self, obs_tuple):
        # Set index to zero if buffer_capacity is exceeded,
        # replacing old records
        index = self.buffer_counter % self.buffer_capacity

        self.state_buffer[index] = obs_tuple[0]
        self.action_buffer[index] = obs_tuple[1]
        self.reward_buffer[index] = obs_tuple[2]
        self.next_state_buffer[index] = obs_tuple[3]

        self.buffer_counter += 1

    # Eager execution is turned on by default in TensorFlow 2. Decorating with tf.function allows
    # TensorFlow to build a static graph out of the logic and computations in our function.
    # This provides a large speed up for blocks of code that contain many small TensorFlow operations such as this one.
    @tf.function
    def update(
        self, state_batch, action_batch, reward_batch, next_state_batch, target_actor, gamma, target_critic, critic_model, critic_optimizer, actor_model, actor_optimizer
    ):
        # Training and updating Actor & Critic networks.
        # See Pseudo Code.
        with tf.GradientTape() as tape:
            target_actions = target_actor(next_state_batch, training=True)
            y = reward_batch + gamma * target_critic(
                [next_state_batch, target_actions], training=True
            )
            critic_value = critic_model([state_batch, action_batch], training=True)
            critic_loss = tf.math.reduce_mean(tf.math.square(y - critic_value))

        critic_grad = tape.gradient(critic_loss, critic_model.trainable_variables)
        critic_optimizer.apply_gradients(
            zip(critic_grad, critic_model.trainable_variables)
        )

        with tf.GradientTape() as tape:
            actions = actor_model(state_batch, training=True)
            critic_value = critic_model([state_batch, actions], training=True)
            # Used `-value` as we want to maximize the value given
            # by the critic for our actions
            actor_loss = -tf.math.reduce_mean(critic_value)

        actor_grad = tape.gradient(actor_loss, actor_model.trainable_variables)
        actor_optimizer.apply_gradients(
            zip(actor_grad, actor_model.trainable_variables)
        )

    # We compute the loss and update parameters
    def learn(self, target_actor, gamma, target_critic, critic_model, critic_optimizer, actor_model, actor_optimizer):
        # Get sampling range
        record_range = min(self.buffer_counter, self.buffer_capacity)
        # Randomly sample indices
        batch_indices = np.random.choice(record_range, self.batch_size)

        # Convert to tensors
        state_batch = tf.convert_to_tensor(list(self.state_buffer[batch_indices]))
        action_batch = tf.convert_to_tensor(self.action_buffer[batch_indices])
        reward_batch = tf.convert_to_tensor(self.reward_buffer[batch_indices])
        reward_batch = tf.cast(reward_batch, dtype=tf.float32)
        next_state_batch = tf.convert_to_tensor(list(self.next_state_buffer[batch_indices]))

        self.update(state_batch, action_batch, reward_batch, next_state_batch, target_actor, gamma, target_critic, critic_model, critic_optimizer, actor_model, actor_optimizer)


# This update target parameters slowly
# Based on rate `tau`, which is much less than one.
@tf.function
def update_target(target_weights, weights, tau):
    for (a, b) in zip(target_weights, weights):
        a.assign(b * tau + a * (1 - tau))


class kerasDeepQLearning(agents.LogicModule):

    def __init__(self
                 , learnerDir
                 , numberOfInputs
                 , numberOfActions
                 , gamma=0.99
                 , epsilon=1.0
                 , minEpsilon=0.1
                 , maxEpsilon=1.0
                 , epsilonInterval = 0.1
                 , learningRate=0.00025
                 , batchSize=32
                 , hiddenLayers=128):
        """Based on this example: https://keras.io/examples/rl/deep_q_network_breakout/"""
        super().__init__()

        self.CoreDir = learnerDir
        self.ModelsDir = self.CoreDir + 'models/'
        self.ModelPath = self.ModelsDir + 'model'

        # Configuration parameters for the whole setup
        self.gamma = gamma  # Discount factor for past rewards
        self.epsilon = epsilon
        self.epsilonInterval = epsilonInterval
        self.maxEpsilon = maxEpsilon
        self.minEpsilon = minEpsilon
        self.batchSize = batchSize
        self.eps = np.finfo(np.float32).eps.item()  # Smallest number such that 1.0 + eps != 1.0

        self.num_inputs = numberOfInputs
        self.num_actions = numberOfActions
        self.num_hidden = hiddenLayers

        self.CurrentStep = 0
        self.max_steps_per_episode = 1

        # Ensure the path exists
        os.makedirs(self.ModelsDir, exist_ok=True)

        if os.path.exists(self.ModelPath):
            self.model = keras.models.load_model(self.ModelPath)
            print('Loading existing model')
        else:

            # Network defined by the Deepmind paper
            # The first model makes the predictions for Q-values which are used to
            # make a action.
            inputs = layers.Input(shape=(84, 84, 4,))

            layer5 = layers.Dense(512, activation="relu")(inputs)
            action = layers.Dense(numberOfActions, activation="linear")(layer5)

            self.model = keras.Model(inputs=inputs, outputs=action)

            # Build a target model for the prediction of future rewards.
            # The weights of a target model get updated every 10000 steps thus when the
            # loss between the Q-values is calculated the target Q-value is stable.
            inputs = layers.Input(shape=(84, 84, 4,))

            layer1 = layers.Conv2D(32, 8, strides=4, activation="relu")(inputs)
            layer2 = layers.Conv2D(64, 4, strides=2, activation="relu")(layer1)
            layer3 = layers.Conv2D(64, 3, strides=1, activation="relu")(layer2)

            layer4 = layers.Flatten()(layer3)

            layer5 = layers.Dense(512, activation="relu")(layer4)
            action = layers.Dense(numberOfActions, activation="linear")(layer5)

            self.target_model = keras.Model(inputs=inputs, outputs=action)

            # In the Deepmind paper they use RMSProp however then Adam optimizer
            # improves training time
            self.optimizer = keras.optimizers.Adam(learning_rate=learningRate, clipnorm=1.0)

        # Experience replay buffers
        self.action_history = []
        self.state_history = []
        self.state_next_history = []
        self.rewards_history = []
        self.episode_reward_history = []
        self.running_reward = 0
        self.episode_count = 0

        # Note: The Deepmind paper suggests 1000000 however this causes memory issues
        self.max_memory_length = 100000
        # Train the model after 4 actions
        self.update_after_actions = 4
        # How often to update the target network
        self.update_target_network = 10000
        # Using huber loss for stability
        self.loss_function = keras.losses.Huber()

        self.lastState = None
        self.lastAction = 0

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info):

        if self.lastState is None:
            self.lastState = observation
        else:

            # Save actions and states in replay buffer
            self.action_history.append(self.lastAction)
            self.state_history.append(observation)
            self.state_next_history.append(self.lastState)
            self.rewards_history.append(reward)

            # Update once batch size is over 32
            if len(self.rewards_history) > self.batchSize:
                # Get indices of samples for replay buffers
                indices = np.random.choice(range(len(self.rewards_history)), size=self.batchSize)

                # Using list comprehension to sample from replay buffer
                state_sample = np.array([self.state_history[i] for i in indices])
                state_next_sample = np.array([self.state_next_history[i] for i in indices])
                rewards_sample = [self.rewards_history[i] for i in indices]
                action_sample = [self.action_history[i] for i in indices]

                # Build the updated Q-values for the sampled future states
                # Use the target model for stability
                future_rewards = self.target_model.predict(state_next_sample)
                # Q value = reward + discount factor * expected future reward
                updated_q_values = rewards_sample + self.gamma * tf.reduce_max(
                    future_rewards, axis=1
                )

                # Create a mask so we only calculate loss on the updated Q-values
                masks = tf.one_hot(action_sample, self.num_actions)

                with tf.GradientTape() as tape:
                    # Train the model on the states and updated Q-values
                    q_values = self.model(state_sample)

                    # Apply the masks to the Q-values to get the Q-value for action taken
                    q_action = tf.reduce_sum(tf.multiply(q_values, masks), axis=1)
                    # Calculate loss between new Q-value and old Q-value
                    loss = self.loss_function(updated_q_values, q_action)

                # Backpropagation
                grads = tape.gradient(loss, self.model.trainable_variables)
                self.optimizer.apply_gradients(zip(grads, self.model.trainable_variables))

            # update the the target network with new weights
            self.target_model.set_weights(self.model.get_weights())

        # Limit the state and reward history
        if len(self.rewards_history) > self.max_memory_length:
            del self.rewards_history[:1]
            del self.state_history[:1]
            del self.state_next_history[:1]
            del self.action_history[:1]

        self.model.save(self.ModelPath)

        # Use epsilon-greedy for exploration
        if self.epsilon > np.random.rand(1)[0]:
            # Take random action
            action = np.random.choice(self.num_actions)
        else:
            # Predict action Q-values
            # From environment state
            state_tensor = tf.convert_to_tensor(list(observation.values()))
            state_tensor = tf.expand_dims(state_tensor, 0)
            action_probs = self.model(state_tensor, training=False)
            # Take best action
            action = tf.argmax(action_probs[0]).numpy()

        # Decay probability of taking random action
        self.epsilon -= self.epsilonInterval
        self.epsilon = max(self.epsilon, self.minEpsilon)

        self.lastAction = action
        self.lastState = observation

        return action
