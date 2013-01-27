# coding=utf-8
#
# $Id: $
#
# NAME:         test_rabbitrpc.py
#
# AUTHOR:       Nick Whalen <nickw@mindstorm-networks.net>
# COPYRIGHT:    2013 by Nick Whalen
# LICENSE:
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# DESCRIPTION:
#   Tests for the rabbitrpc module.
#

import mock
import pytest
import cPickle
from rabbitrpc import rpcserver


class Test___init__(object):
    """
    Tests __init__

    """
    def setup_method(self, method):
        """
        Test setup.

        :param method:

        """
        self.host = 'hostname'
        self.port = 1234
        self.vhost = 'b/b'

        self.connection_settings = {
            'host': self.host,
            'port': self.port,
            'virtual_host': self.vhost,
        }
        self.default_settings = {
            'host': 'localhost',
            'port': 5672,
            'virtual_host': '/',
        }
        self.localrpc = reload(rpcserver)


        self.callback = mock.MagicMock()
        self.queue = 'testRPC'
        self.localrpc.RPCServer._configureConnection = mock.MagicMock()
        self.localrpc.logging = mock.MagicMock()

        self.rpc = self.localrpc.RPCServer(self.callback, self.queue)
    #---

    def test_SetsUpLogger(self):
        """
        Tests that __init__ setts up a logging instance.

        """
        called = self.localrpc.logging.getLogger.called
        assert called == True
    #---

    def test_SetsRPCCallbackMethod(self):
        """
        Tests that __init__ sets the rpc_callback.

        """
        assert self.rpc.rpc_callback == self.callback
    #---

    def test_SetsQueueName(self):
        """
        Tests that __init__ sets the incoming rpc queue.

        """
        assert self.rpc.queue == self.queue
    #---

    def test_SetsDefaultConnectionSettings(self):
        """
        Tests that __init__ sets the following default config:
            host: localhost
            port: 5672
            virtual_host: /

        """
        assert self.rpc.connection_settings == self.default_settings
    #---

    def test_ProvidedConnectionSettingsOverrideDefaultConnectionSettings(self):
        """
        Tests that __init__ overrides the default connection settings if they are provided by the user.

        """
        rpc = self.localrpc.RPCServer(self.callback, self.queue, connection_settings=self.connection_settings)
        assert rpc.connection_settings == self.connection_settings
    #---

    def test_RemovesUsernameFromConnectionSettings(self):
        """
        Tests that __init__ removes the username from the connection settings.

        """
        rpc = self.localrpc.RPCServer(self.callback, self.queue, connection_settings=self.connection_settings)
        assert 'username' not in rpc.connection_settings
    #---

    def test_RemovesPasswordFromConnectionSettings(self):
        """
        Tests that __init__ removes the password from the connection settings.

        """
        rpc = self.localrpc.RPCServer(self.callback, self.queue, connection_settings=self.connection_settings)
        assert 'password' not in rpc.connection_settings
    #---

    def test_SetsExchangeToProvidedParamIfExists(self):
        """
        Tests that __init__ sets the exchange to what was passed in, if something was passed in.

        """
        exchange = 'BobXchange'
        rpc = rpcserver.RPCServer(self.callback, self.queue, exchange)

        assert rpc.exchange == exchange
    #---

    def test_DefaultExchangeIsBlankString(self):
        """
        Tests that __init__ sets the default exchange to '' if an exchange was not passed in.

        """
        exchange = ''
        rpc = rpcserver.RPCServer(self.callback, self.queue)

        assert rpc.exchange == exchange
    #---

    def test_CallsConnectionSetup(self):
        """
        Tests that __init__ calls the connection setup.

        """
        self.rpc._configureConnection.assert_called_once_with()
    #---
#---

class Test_stop(object):
    """
    Tests the stop method.

    """
    def setup_method(self, method):
        """
        Test setup.

        :param method:

        """
        localrpc = reload(rpcserver)
        self.callback = mock.MagicMock()
        localrpc.RPCServer._configureConnection = mock.MagicMock()

        self.rpc = localrpc.RPCServer(self.callback, '')
        self.rpc.channel = mock.MagicMock()

        self.rpc.stop()
    #---

    def test_StopsConsumer(self):
        """
        Tests that stop stops the RabbitMQ consumer

        """
        self.rpc.channel.stop_consuming.assert_called_once_with()
    #---

    def test_DisconnectsFromServer(self):
        """
        Tests that stop disconnects from the RabbitMQ server.

        """
        self.rpc.channel.close.assert_called_once_with()
    #---
#---

class Test_run(object):
    """
    Tests the run method.

    """
    def setup_method(self, method):
        """
        Setup tests.

        :param method:

        """
        localrpc = reload(rpcserver)
        self.callback = mock.MagicMock()
        localrpc.RPCServer._configureConnection = mock.MagicMock()

        self.rpc = localrpc.RPCServer(self.callback, '')
        self.rpc._connect = mock.MagicMock()
        self.rpc.channel = mock.MagicMock()

        self.rpc.run()
    #---

    def test_CallsInternalConnectMethod(self):
        """
        Tests that run calls the internal _connect method to establish a RabbitMQ connection.

        """
        self.rpc._connect.assert_called_once_with()
    #---

    def test_StartsConsumer(self):
        """
        Tests that run starts the RabbitMQ consumer.

        """
        self.rpc.channel.start_consuming.assert_called_once_with()
    #---
#---

class Test__consumerCallback(object):
    """
    Tests the _consumerCallback method.

    """
    def setup_method(self, method):
        """
        Test setup.  Fair warning, there's a crazy amount of stuff in this one.

        :param method:

        """
        self.body = {'bob':'barker'}
        self.body_pickled = cPickle.dumps(self.body)
        self.rpc_response = {'rpc':'result'}
        self.rpc_response_pickled = cPickle.dumps(self.rpc_response)
        self.exchange = 'Xchange'
        self.basic_props = 'Props'

        # Global mocking
        self.localrpc = reload(rpcserver)
        self.callback = mock.MagicMock(return_value=self.rpc_response)
        self.localrpc.RPCServer._configureConnection = mock.MagicMock()
        self.localrpc.pika.BasicProperties = mock.MagicMock(return_value=self.basic_props)
        self.BasicProperties = self.localrpc.pika.BasicProperties

        # Initialize class and mock methods/properties
        self.rpc = self.localrpc.RPCServer(self.callback, '')
        self.rpc.channel = mock.MagicMock()
        self.rpc.exchange = self.exchange
        self.method = mock.MagicMock()
        self.props = mock.MagicMock()

        # Property mocks for the _consumerCallback method parameters
        self.reply_to = 'bob.bob'
        type(self.props).reply_to = mock.PropertyMock(return_value = self.reply_to)

        self.delivery_tag = 'taggems'
        type(self.method).delivery_tag = mock.PropertyMock(return_value = self.delivery_tag)

        self.correlation_id = 'adk23rflb'
        type(self.props).correlation_id = mock.PropertyMock(return_value = self.correlation_id)

        # Actual call for method under test
        self.rpc._consumerCallback('', self.method, self.props, self.body_pickled)
    #---

    def _reload_cPickle(self, test_method):
        """
        Wraps a test method that uses cPickle mocking so it doesn't screw up other tests.
        """
        cpickle = reload(rpcserver.cPickle)
        self.localrpc.cPickle = cpickle

        try:
            test_method()
        except Exception:
            raise
        finally:
            self.localrpc.cPickle = reload(rpcserver.cPickle)
    #---


    def test_CallsProvidedCallback(self):
        """
        Tests that _consumerCallback calls the provided callback with un-pickled data.

        """
        self.rpc.rpc_callback.assert_called_once_with(self.body)
    #---

    # Uses cPickle reload wrapper
    def _UnPicklesBody(self):
        """
        Tests that _consumerCallback will un-pickle the message body.

        """
        self.localrpc.cPickle.loads = mock.MagicMock(return_value=self.body)
        self.rpc._consumerCallback('', self.method, self.props, self.body_pickled)

        self.localrpc.cPickle.loads.assert_called_once_with(self.body_pickled)
    #---
    def test_UnPicklesBody(self): self._reload_cPickle(self._UnPicklesBody)

    # Uses cPickle reload wrapper
    def _PicklesRPCCallbackResponse(self):
        """
        Tests that _consumerCallback pickles the RPC callback's response

        """
        self.localrpc.cPickle.dumps = mock.MagicMock(return_value=self.rpc_response_pickled)
        self.rpc._consumerCallback('', self.method, self.props, self.body_pickled)

        self.localrpc.cPickle.dumps.assert_called_once_with(self.rpc_response)
    #---
    def test_PicklesRPCCallbackResponse(self): self._reload_cPickle(self._PicklesRPCCallbackResponse)

    # Uses cPickle reload wrapper
    def _LogsUnexpectedUnPickleExceptions(self):
        """
        Tests that _consumerCallback will log unexpected exceptions arising from the cPickle loads method.

        """
        self.localrpc.cPickle.loads = mock.MagicMock(side_effect=ValueError(), return_value=self.body)
        self.rpc.log.error = mock.MagicMock()
        self.rpc._consumerCallback('', self.method, self.props, self.body_pickled)

        called = self.rpc.log.error.called
        assert called == True

    #---
    def test_LogsUnexpectedUnPickleExceptions(self): self._reload_cPickle(self._LogsUnexpectedUnPickleExceptions)

    def test_LogsUnexpectedRPCCallbackExceptions(self):
        """
        Tests that _consumerCallback will log unexpected exceptions arising from the RPC callback method.

        """
        self.callback.side_effect = ValueError()
        self.rpc.log.error = mock.MagicMock()
        self.rpc._consumerCallback('', self.method, self.props, self.body_pickled)

        called = self.rpc.log.error.called
        assert called == True
    #---

    def test_DoesNotReplyIfReplyToIsNotSet(self):
        """
        Tests that _consumerCallback does not send a RPC reply if the incoming message's reply_to is not set.

        """
        self.rpc.channel.reset_mock()
        props = {}

        self.rpc._consumerCallback('', self.method, props, self.body_pickled)

        called = self.rpc.channel.basic_publish.called
        assert called == False
    #---


    def test_GeneratesPublishProperties(self):
        """
        Tests that _consumerCallback calls the provided callback.

        """
        self.BasicProperties.assert_called_once_with(delivery_mode=2, correlation_id=self.correlation_id)
    #---

    def test_CallsBasicPublish(self):
        """
        Tests that _consumerCallback calls basic_publish with the appropriate arguments.

        """
        self.rpc.channel.basic_publish.assert_called_once_with(exchange=self.exchange, routing_key=self.reply_to,
                                                           properties=self.basic_props, body=self.rpc_response_pickled)
    #---

    def test_AcknowledgesMessage(self):
        """
        Tests that _consumerCallback calls basic_ack so RabbitMQ knows the message has been processed.

        """
        self.rpc.channel.basic_ack.assert_called_once_with(delivery_tag=self.delivery_tag)
    #---
#---

class Test__connect(object):
    """
    Tests the _connect method.

    """
    def setup_method(self, method):
        """
        Setup tests

        :param method:

        """
        self.connection_params = {'none':None}
        self.queue = 'daQueue'

        localrpc = reload(rpcserver)
        self.callback = mock.MagicMock()
        localrpc.RPCServer._configureConnection = mock.MagicMock()

        self.channel = mock.MagicMock()
        self.connection = mock.MagicMock()
        self.connection.channel.return_value=self.channel
        localrpc.pika.BlockingConnection = mock.MagicMock(return_value=self.connection)
        self.BlockingConnection = localrpc.pika.BlockingConnection

        self.rpc = localrpc.RPCServer(self.callback, self.queue)
        self.rpc.connection_params = self.connection_params

        self.rpc._connect()
    #---

    def test_UsesBlockingConnection(self):
        """
        Tests that _connect calls pika.BlockingConnection.

        """
        self.BlockingConnection.assert_called_once_with(self.connection_params)
    #---

    def test_RaisesConnectionErrorIfConnectionProblem(self):
        """
        Tests that _connect raises ConnectionError if there is a problem connecting to RabbitMQ.

        """
        self.BlockingConnection.side_effect = rpcserver.AMQPConnectionError

        with pytest.raises(rpcserver.ConnectionError):
            self.rpc._connect()
    #---

    def test_CreatesChannelOnConnection(self):
        """
        Tests that _connect creates a new channel on the connection.

        """
        self.connection.channel.assert_called_once_with()
    #---

    def test_DeclaresDurableQueue(self):
        """
        Tests that _connect declares a durable queue.

        """
        self.channel.queue_declare.assert_called_once_with(queue=self.queue, durable=True)
    #---

    def test_SetsQoSPrefetchCount(self):
        """
        Tests that _connect sets a prefetch_count of 1 for basic_qos.

        """
        self.channel.basic_qos.assert_called_once_with(prefetch_count=1)
    #---

    def test_SetsUpConsumer(self):
        """
        Tests that _connect sets up the consumer with the callback and queue name.

        """
        self.channel.basic_consume.assert_called_once_with(self.rpc._consumerCallback, queue=self.rpc.queue)
    #---
#---


class Test__configureConnection(object):
    """
    Tests the _configureConnection method.
    """
    def setup_method(self, method):
        """
        Setup Tests

        :param method:

        """
        self.host = 'hostname'
        self.port = 1234
        self.vhost = 'b/b'

        self.connection_settings = {
            'host': self.host,
            'port': self.port,
            'virtual_host': self.vhost,
        }
        self.localrpc = reload(rpcserver)

        self.localrpc.pika.ConnectionParameters = mock.MagicMock(return_value=self.connection_settings)


        self.callback = mock.MagicMock()
        self.rpc = self.localrpc.RPCServer(self.callback, '', connection_settings=self.connection_settings)
    #---

    def test_SetsConnectionParameters(self):
        """
        Tests that _configureConnection sets the class' connection parameters.

        """
        assert self.rpc.connection_settings == self.connection_settings
    #---
#---

class Test__createCredentials(object):
    """
    Tests the _createCredentials method.

    """
    def setup_method(self, method):
        """
        Setup Tests

        :param method:

        """
        self.username = 'bob'
        self.password = 'barker'
        self.creds = {self.username:self.password}

        self.connection_settings = {
            'username': self.username,
            'password': self.password,
        }
        localrpc = reload(rpcserver)

        localrpc.pika.PlainCredentials = mock.MagicMock(return_value=self.creds)
        self.PlainCredentials = localrpc.pika.PlainCredentials

        localrpc.RPCServer._configureConnection = mock.MagicMock()

        self.callback = mock.MagicMock()
        # Calls _createCredentials if username and password are set
        self.rpc = localrpc.RPCServer(self.callback, '', connection_settings=self.connection_settings)
    #---

    def test_CreatesPlainCredentialsObject(self):
        """
        Tests that _createCredentials creates a new pika.PlainCredentials object based on the provided username
        and password.

        """
        self.PlainCredentials.assert_called_once_with(self.username, self.password)
    #---

    def test_StoresCredentialsInConnectionSettings(self):
        """
        Tests that _createCredentials sets the credentials in the connection config to the PlainCredentials object.

        """
        assert self.rpc.connection_settings['credentials'] == self.creds
    #---
#---