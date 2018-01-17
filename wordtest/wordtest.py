# https://machinelearningmastery.com/use-word-embedding-layers-deep-learning-keras/
# https://qiita.com/yagays/items/292dd04c53cb7e0bcb5a

# 分類分け

from keras.preprocessing.text import one_hot
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
from keras.layers import Dense, LSTM
from keras.layers import Flatten
from keras.layers.embeddings import Embedding

# define documents
docs = ['Well done!',
		'Good work',
		'Great effort',
		'nice work',
		'Excellent!',
		'Weak',
		'Poor effort!',
		'not good',
		'poor work',
		'Could have done better.']
# define class labels
labels = [1,1,1,1,1,0,0,0,0,0]


# integer encode the documents (50種類の言葉）
vocab_size = 50
encoded_docs = [one_hot(d, vocab_size) for d in docs]
print(encoded_docs)

# pad documents to a max length of 4 words
max_length = 4
padded_docs = pad_sequences(encoded_docs, maxlen=max_length, padding='post')
print(padded_docs)

# define the model
model = Sequential()
# vocabulary of 50 and an input length of 4
# the output from the Embedding layer will be 4 vectors of 8 dimensions each, one for each word.
model.add(Embedding(vocab_size, 8, input_length=max_length))
# We flatten this to a one 32-element vector to pass on to the Dense output layer.
model.add(LSTM(32))
model.add(Dense(1, activation='sigmoid'))
# compile the model
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])
# summarize the model
print(model.summary())


# fit the model
model.fit(padded_docs, labels, epochs=100, verbose=0)
# evaluate the model
loss, accuracy = model.evaluate(padded_docs, labels, verbose=0)
print('Accuracy: %f' % (accuracy*100))


result = model.predict_proba(padded_docs)
print(result)