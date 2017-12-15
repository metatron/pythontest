import tensorflow as tf
import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

sess = tf.InteractiveSession()


x_ = [[0,0],[0,1],[1,0],[1,1]]
expect=[[1,0],[0,1],[0,1],[1,0]] #[1,0]==0 [0,1]==1

x = tf.placeholder("float", [None, 2])
y_ = tf.placeholder("float", [None, 2]) # two output classes

number_hiddeon_nodes = 20

W = tf.Variable(tf.random_uniform([2, number_hiddeon_nodes], -0.01, 0.01))
b = tf.Variable(tf.random_uniform([number_hiddeon_nodes], -0.01, 0.01))
hidden = tf.nn.relu(tf.matmul(x,W) + b) # first layer

W2 = tf.Variable(tf.random_uniform([number_hiddeon_nodes, 2], -0.01, 0.01))
b2 = tf.Variable(tf.zeros([2]))
hidden2 = tf.matmul(hidden, W2)#+b2

y = tf.nn.softmax(hidden2)


# Define loss and optimizer
cross_entropy = -tf.reduce_sum(y_*tf.log(y))
train_step = tf.train.GradientDescentOptimizer(0.2).minimize(cross_entropy)

# Train
tf.initialize_all_variables().run()
for step in range(1000):
    feed_dict={x:x_, y_:expect}
    e,a=sess.run([cross_entropy, train_step], feed_dict)
    if e < 1: break  # early stopping yay
    print ("step %d : entropy %s" % (step, e))  # error/loss should decrease over time