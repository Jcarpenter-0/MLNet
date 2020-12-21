import learners.common

import os
import numpy as np
from sklearn import preprocessing
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


class kerasActorCritic(learners.common.MLModule):

    def __init__(self
                 , learnerDir
                 , numberOfInputs
                 , numberOfActions
                 , gamma=0.99
                 , hiddenLayers=128):
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
            print('Loading existing model')
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

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info, domainDefinition:learners.common.DomainModule):

        episode_reward = 0

        print('Obv {} Rew {}'.format(observation, reward))

        with tf.GradientTape() as tape:
            # normalize the values

            stateRaw = list(observation.values())

            state = tf.convert_to_tensor(stateRaw)
            state = tf.expand_dims(state, 0)

            state = preprocessing.normalize(X=state, norm='l2', axis=1)

            # Predict action probabilities and estimated future rewards
            # from environment state
            action_probs, critic_value = self.model(state)
            self.critic_value_history.append(critic_value[0, 0])

            # Sample action from action probability distribution
            action = np.random.choice(self.num_actions, p=np.squeeze(action_probs))

            print('State {} - ActionSpace {} - Action {}'.format(state, np.squeeze(action_probs), action))

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

        return actionSpace[action]
