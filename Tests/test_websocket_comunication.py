import time, json, uuid, pytest, asyncio
from unittest import mock
from datetime import datetime
from StateHandler import States
from websocket_communication import WebSocket , CHARGER_VARIABLES, RESERVATION_VARIABLES
from variables.charger_variables import Charger

TEST_CHARGER_STATUS = ["Available","Missing"] #Add the correct states

TEST_RECIEVED_MESSAGES = [
    [2, '100009DataTransfer1664971239072', 'ReserveNow'],
    [3, '0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v', 'BootNotification', {
    'status': 'Accepted'}],
    [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "RemoteStartTransaction"],
    [3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "RemoteStopTransaction"],
    [2, '100009DataTransfer1664971239072', 'DataTransfer'],
    [3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction"],
    [3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "NotImplemented", "Not Implemented"],
    #[3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction"],
    [3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "Authorize"],
    [3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "MeterValues"],
    ]

TEST_DATA_TRANSFER_MESSAGES = [
    [[2, '100009DataTransfer1664971239072', 'DataTransfer', {
        'vendorId': 'com.flexicharge', 
        'messageId': 'BootData', 
        'data': '{"chargerId":100009,"chargingPrice":"5.25"}'}],"Accepted"],
    [[2, '100009DataTransfer1664971239072', 'DataTransfer', {
        'vendorId': 'com.flexicharge', 
        'messageId': 'DataTransfer', 
        'data': ''}],"Rejected"]
]

class TestWebSocket:
     
    @pytest.fixture
    def websocket_instance(self):
        return WebSocket()

    @pytest.mark.parametrize("charger_test_status",TEST_CHARGER_STATUS)
    def test_get_status(self,charger_test_status,websocket_instance):
        #Arrange
        pre_test_state = CHARGER_VARIABLES.status

        CHARGER_VARIABLES.status = charger_test_status
        assert CHARGER_VARIABLES.status is charger_test_status
        #Act
        fetched_status = websocket_instance.get_status()

        #Assert
        assert fetched_status == charger_test_status
        
        #clean up
        CHARGER_VARIABLES.status = pre_test_state

    @pytest.mark.parametrize("state",[[True],[False]])
    def test_is_closed(self, state, websocket_instance):
        #Arrange
        test_state = state
        def mock_is_closed():
            nonlocal test_state
            return test_state

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.closed = mock_is_closed()
        #Act
        result = websocket_instance.is_closed()
        
        #Assert
        assert test_state == result
        
    def test_set_websocket(self, websocket_instance):
        #Arrange
        websocket_instance._webSocket = mock.Mock()
        
        assert websocket_instance._webSocket is not None
        
        #Act
        websocket_instance.set_websocket(None)
        
        #Assert
        assert websocket_instance._webSocket is None

    @pytest.mark.asyncio
    async def test_start_websocket(self, websocket_instance):
        """
        Test that the WebSocket connection is started correctly.
        """
        #Arrange
        with mock.patch('websocket_communication.ws.connect') as mock_connect:
            mock_connect.return_value = asyncio.Future()
            mock_connect.return_value.set_result(None)
            #Act
            await websocket_instance.start_websocket()
            #Assert
            mock_connect.assert_called_once_with(
                'ws://127.0.0.1:60003', subprotocols=['ocpp1.6'], ping_interval=5, timeout=None
            )

    @pytest.mark.asyncio
    async def test_send_message(self, websocket_instance):
        """
        Test to check that the Send Message funktion forwards messages acordingaly
        """
        #Arrange
        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send

        json_message = '{"key":"value"}'
        
        #Act
        await websocket_instance.send_message(json_message)

        #Assert
        assert message_sent is not None
        assert message_sent == json_message

    @pytest.mark.asyncio
    @pytest.mark.parametrize("charger_status",TEST_CHARGER_STATUS)
    async def test_send_status_notification(self,charger_status,websocket_instance):
        #Arrenge
        pre_test_state = CHARGER_VARIABLES.status

        CHARGER_VARIABLES.status = charger_status
        assert CHARGER_VARIABLES.status is charger_status

        message_sent = None

        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send
        

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StatusNotification", {
            "connectorId": "1",
            "errorCode": "",
            "status": charger_status
        }]
        expected_message = json.dumps(msg)

        #Act
        await websocket_instance.send_status_notification()
        
        #Assert
        assert message_sent is not None
        assert message_sent == expected_message

        #Clean up
        CHARGER_VARIABLES.status = pre_test_state
    
    @pytest.mark.asyncio
    async def test_listen_for_response(self,websocket_instance):
        #Arrange
        sent_message = {
            "key":"value"
            }
        json_sent_message = json.dumps(sent_message)
        
        async def mock_recv():
            await asyncio.sleep(0.1)

            nonlocal json_sent_message
            return json_sent_message

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.recv = mock_recv 
        
        #Act
        recived_message = await websocket_instance.listen_for_response()

        #Assert
        assert recived_message == sent_message
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_message",TEST_RECIEVED_MESSAGES)
    async def test_handle_message(self,test_message,websocket_instance,capsys):
        #Arrange
        was_reserv_now = False
        was_RemoteStartTransaction = False
        was_RemoteStopTransaction = False
        was_DataTransfer = False

        async def mock_reserve_now(message):
            nonlocal was_reserv_now
            was_reserv_now = True
            print(message)
            
        async def mock_remote_start_transaction(message):
            nonlocal was_RemoteStartTransaction
            was_RemoteStartTransaction = True
            print(message)

        async def mock_remote_stop_transaction(message):
            nonlocal was_RemoteStopTransaction
            was_RemoteStopTransaction = True
            print(message)

        async def mock_data_transfer_response(message):
            nonlocal was_DataTransfer
            was_DataTransfer = True
            print(message)
            
        websocket_instance._webSocket = mock.Mock()

        websocket_instance.reserve_now = mock_reserve_now
        websocket_instance.remote_start_transaction = mock_remote_start_transaction
        websocket_instance.remote_stop_transaction = mock_remote_stop_transaction
        websocket_instance.data_transfer_response = mock_data_transfer_response

        #Act
        await websocket_instance.handle_message(test_message)

        #Assert
        printed = capsys.readouterr()
        output = printed.out.split('\n')
        
        if test_message[2] == "ReserveNow":
            assert was_reserv_now
        
        elif test_message[2] == "BootNotification":
            end_result = f"Was: {test_message[3]['status']}"
            assert end_result in output
            
        elif test_message[2] == "RemoteStartTransaction":
            assert was_RemoteStartTransaction
        
        elif test_message[2] == "RemoteStopTransaction":
            assert was_RemoteStopTransaction
        
        elif test_message[2] == "DataTransfer":
            assert was_DataTransfer
        
        elif test_message[2] == "StartTransaction":
            assert websocket_instance.transaction_id == 347
        
        elif test_message[2] == "NotImplemented":
            assert test_message[3] == "Not Implemented"
        
        elif test_message[2] == "StopTransaction":
            assert False, "This funktion is not implemented"
        
        elif test_message[2] == "Authorize":
            end_result = "Could not handle message"
            assert str(test_message) in output
            assert end_result in output

        elif test_message[2] == "MeterValues":
            end_result = "Could not handle message"
            assert str(test_message) in output
            assert end_result in output

        else:
            assert False, "if this is reached then the test_message contains a unknown command for the funktion"
    
    @pytest.mark.parametrize("test_data_is_charging, test_data_charging_id_tag, test_data_charging_connector, test_data_charger_id, test_data_charging_Wh, test_data_charging_Wh_per_second, test_data_charging_price, test_data_current_charging_percentage, test_data_current_charge_time_left, test_data_meter_value_total, test_data_status, test_data_state",[
                                    [
                                        False,
                                        None, 
                                        None, 
                                        100002,
                                        0, 
                                        0.3, 
                                        0.0, 
                                        0, 
                                        CHARGER_VARIABLES._current_charge_time_left, 
                                        0, 
                                        "Available",
                                        States.S_STARTUP],
                                    [
                                        False,
                                        None, 
                                        None, 
                                        100001, 
                                        0, 
                                        0.3, 
                                        0.0, 
                                        0, 
                                        CHARGER_VARIABLES._current_charge_time_left, 
                                        0, 
                                        "Missing",
                                        States.S_CHARGING
                                    ]
                             ])
    def test_get_charger_variables(self,websocket_instance,test_data_is_charging,test_data_charging_id_tag,test_data_charging_connector,test_data_charger_id,test_data_charging_Wh,test_data_charging_Wh_per_second,test_data_charging_price,test_data_current_charging_percentage,test_data_current_charge_time_left,test_data_meter_value_total,test_data_status,test_data_state):
        #Arrange
        #save pre test values 
        pre_test_is_charging                 = CHARGER_VARIABLES._is_charging 
        pre_test_charging_id_tag             = CHARGER_VARIABLES._charging_id_tag 
        pre_test_charging_connector          = CHARGER_VARIABLES._charging_connector 
        pre_test_charger_id                  = CHARGER_VARIABLES._charger_id
        pre_test_charging_Wh                 = CHARGER_VARIABLES._charging_Wh 
        pre_test_charging_Wh_per_second      = CHARGER_VARIABLES._charging_Wh_per_second 
        pre_test_charging_price              = CHARGER_VARIABLES._charging_price 
        pre_test_current_charging_percentage = CHARGER_VARIABLES._current_charging_percentage 
        pre_test_current_charge_time_left    = CHARGER_VARIABLES._current_charge_time_left 
        pre_test_meter_value_total           = CHARGER_VARIABLES._meter_value_total 
        pre_test_status                      = CHARGER_VARIABLES._status 
        pre_test_state                       = CHARGER_VARIABLES._state
        
        #set CHARGER_VARIABLES to expected data
        CHARGER_VARIABLES._is_charging                 = test_data_is_charging
        CHARGER_VARIABLES._charging_id_tag             = test_data_charging_id_tag
        CHARGER_VARIABLES._charging_connector          = test_data_charging_connector
        CHARGER_VARIABLES._charger_id                  = test_data_charger_id
        CHARGER_VARIABLES._charging_Wh                 = test_data_charging_Wh  
        CHARGER_VARIABLES._charging_Wh_per_second      = test_data_charging_Wh_per_second
        CHARGER_VARIABLES._charging_price              = test_data_charging_price
        CHARGER_VARIABLES._current_charging_percentage = test_data_current_charging_percentage
        CHARGER_VARIABLES._current_charge_time_left    = test_data_current_charge_time_left
        CHARGER_VARIABLES._meter_value_total           = test_data_meter_value_total 
        CHARGER_VARIABLES._status                      = test_data_status
        CHARGER_VARIABLES._state                       = test_data_state
        
        #Act
        Uppdateted_charger_variables = websocket_instance.get_charger_variables()
        
        #Assert
        assert Uppdateted_charger_variables is CHARGER_VARIABLES 
        assert Uppdateted_charger_variables._is_charging                 == CHARGER_VARIABLES._is_charging
        assert Uppdateted_charger_variables._charging_id_tag             == CHARGER_VARIABLES._charging_id_tag
        assert Uppdateted_charger_variables._charging_connector          == CHARGER_VARIABLES._charging_connector
        assert Uppdateted_charger_variables._charger_id                  == CHARGER_VARIABLES._charger_id
        assert Uppdateted_charger_variables._charging_Wh                 == CHARGER_VARIABLES._charging_Wh
        assert Uppdateted_charger_variables._charging_Wh_per_second      == CHARGER_VARIABLES._charging_Wh_per_second
        assert Uppdateted_charger_variables._charging_price              == CHARGER_VARIABLES._charging_price
        assert Uppdateted_charger_variables._current_charging_percentage == CHARGER_VARIABLES._current_charging_percentage
        assert Uppdateted_charger_variables._current_charge_time_left    == CHARGER_VARIABLES._current_charge_time_left
        assert Uppdateted_charger_variables._meter_value_total           == CHARGER_VARIABLES._meter_value_total
        assert Uppdateted_charger_variables._status                      == CHARGER_VARIABLES._status
        assert Uppdateted_charger_variables._state                       == CHARGER_VARIABLES._state
        
        #clean up
        #Return the global variables to the pre test values
        CHARGER_VARIABLES._is_charging                 = pre_test_is_charging
        CHARGER_VARIABLES._charging_id_tag             = pre_test_charging_id_tag
        CHARGER_VARIABLES._charging_connector          = pre_test_charging_connector
        CHARGER_VARIABLES._charger_id                  = pre_test_charger_id
        CHARGER_VARIABLES._charging_Wh                 = pre_test_charging_Wh 
        CHARGER_VARIABLES._charging_Wh_per_second      = pre_test_charging_Wh_per_second
        CHARGER_VARIABLES._charging_price              = pre_test_charging_price
        CHARGER_VARIABLES._current_charging_percentage = pre_test_current_charging_percentage
        CHARGER_VARIABLES._current_charge_time_left    = pre_test_current_charge_time_left
        CHARGER_VARIABLES._meter_value_total           = pre_test_meter_value_total 
        CHARGER_VARIABLES._status                      = pre_test_status
        CHARGER_VARIABLES._state                       = pre_test_state
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_data_is_reserved,test_data_status,test_data_reservation_id_tag,test_data_reservation_id,test_data_reserved_connector",[
        [False, 'Available', 1, None, None],
        [True, 'Missing', 10, None, None]
        ])
    async def test_get_reservation_info(self,websocket_instance,test_data_is_reserved,test_data_status,test_data_reservation_id_tag,test_data_reservation_id,test_data_reserved_connector):
        #Arrange
        pre_test_reservation_is_reserved = RESERVATION_VARIABLES.is_reserved
        pre_test_charger_status = CHARGER_VARIABLES.status
        pre_test_reservation_reservation_id_tag = RESERVATION_VARIABLES.reservation_id_tag
        pre_test_reservation_reservation_id = RESERVATION_VARIABLES.reservation_id
        pre_test_reservation_reserved_connector = RESERVATION_VARIABLES.reserved_connector
        
        RESERVATION_VARIABLES.is_reserved = test_data_is_reserved
        CHARGER_VARIABLES.status = test_data_status
        RESERVATION_VARIABLES.reservation_id_tag = test_data_reservation_id_tag
        RESERVATION_VARIABLES.reservation_id = test_data_reservation_id
        RESERVATION_VARIABLES.reserved_connector = test_data_reserved_connector

        #Act
        reservation_info = await websocket_instance.get_reservation_info()
        #Assert
        assert test_data_is_reserved == reservation_info[0]
        assert test_data_status == reservation_info[1]
        assert test_data_reservation_id_tag == reservation_info[2]
        assert test_data_reservation_id == reservation_info[3]
        assert test_data_reserved_connector == reservation_info[4]
        #clean up
        RESERVATION_VARIABLES.is_reserved = pre_test_reservation_is_reserved
        CHARGER_VARIABLES.status = pre_test_charger_status
        RESERVATION_VARIABLES.reservation_id_tag = pre_test_reservation_reservation_id_tag
        RESERVATION_VARIABLES.reservation_id = pre_test_reservation_reservation_id
        RESERVATION_VARIABLES.reserved_connector = pre_test_reservation_reserved_connector
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("message_id,message_data,test_transaction_id",[
        ["0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v","Suposed to be latest meter value",1],
        ["0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8t","Suposed to be latest meter value",2]
        ])
    async def test_data_transfer_request(self,websocket_instance,message_id,message_data,test_transaction_id):
        """
        Test that the data transfer request is sent correctly
        """
        #Arrenge
        test_data = (f"{{\"transactionID\":{test_transaction_id},\"latestMeterValue\":{message_data},\"CurrentChargePercentage\":{message_data}}}")
        
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "DataTransfer", {
            "vendorId": "com.flexicharge",
            "messageId": "BootData",
            "data": test_data}]
        expected_message = json.dumps(msg)

        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send
        websocket_instance.transaction_id = test_transaction_id
        
        #Act
        await websocket_instance.data_transfer_request(message_id,message_data)
        
        #Assert
        assert message_sent is not None
        assert message_sent == expected_message
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("data_transfer_message,expected_status",TEST_DATA_TRANSFER_MESSAGES)
    async def test_data_transfer_response(self, websocket_instance,data_transfer_message,expected_status):
        #Arrange
        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send

        #Act
        await websocket_instance.data_transfer_response(data_transfer_message)
        
        #Assert
        assert message_sent is not None
        
        message = json.loads(message_sent)
        assert message[3]["status"] == expected_status
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_is_remote,test_charging_connector,charging_id_tag,reservation_id",[
                            [True, "1", 23, 23123]])
    async def test_start_transaction(self, websocket_instance, test_is_remote, test_charging_connector, charging_id_tag, reservation_id):
        #Arrange
        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send
        
        assert CHARGER_VARIABLES.meter_value_total == 0

        pre_test_charging_connector = CHARGER_VARIABLES.charging_connector
        pre_test_charging_id_tag = CHARGER_VARIABLES.charging_id_tag
        pre_test_reservation_id = RESERVATION_VARIABLES.reservation_id
        
        
        CHARGER_VARIABLES.charging_connector     = test_charging_connector
        CHARGER_VARIABLES.charging_id_tag        = charging_id_tag
        RESERVATION_VARIABLES.reservation_id     = reservation_id
        
        test_timestamp = datetime.now().timestamp()

        Expected_Message = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction", {
                "connectorId": CHARGER_VARIABLES.charging_connector,
                "id_tag": CHARGER_VARIABLES.charging_id_tag,
                "meterStart": CHARGER_VARIABLES.meter_value_total,
                "timestamp": test_timestamp,
                "reservationId": RESERVATION_VARIABLES.reservation_id,
            }]
        
        #Act
        await websocket_instance.start_transaction(test_is_remote)
        print(datetime.fromtimestamp(1695740934.543119))
        print(datetime.fromtimestamp(1695740934.54212))
        #Assert
        assert message_sent is not None
        sent_message = json.loads(message_sent)
        assert sent_message[0] == Expected_Message[0]
        assert sent_message[1] == Expected_Message[1]
        assert sent_message[2] == Expected_Message[2]
        assert sent_message[3]["connectorId"] == Expected_Message[3]["connectorId"]
        assert sent_message[3]["id_tag"] == Expected_Message[3]["id_tag"]
        assert sent_message[3]["meterStart"] == Expected_Message[3]["meterStart"]
        assert sent_message[3]["timestamp"] == pytest.approx(Expected_Message[3]["timestamp"],0.002)
        assert sent_message[3]["reservationId"] == Expected_Message[3]["reservationId"]
        #clean up

        CHARGER_VARIABLES.charging_connector     = pre_test_charging_connector
        CHARGER_VARIABLES.charging_id_tag        = pre_test_charging_id_tag
        RESERVATION_VARIABLES.reservation_id     = pre_test_reservation_id
        
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_is_remote,test_charging_id_tag,test_transaction_id",[
                            [True, 23, 1],
                            [True, 23, 1]])
    async def test_stop_transaction(self, test_is_remote, websocket_instance,test_charging_id_tag,test_transaction_id):
        #Arrange
        test_timestamp = datetime.now().timestamp()

        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        async def mock_status_notification():
            pass

        websocket_instance.send_status_notification = mock_status_notification
        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send

        assert CHARGER_VARIABLES.meter_value_total == 0

        pre_test_charging_id = CHARGER_VARIABLES.charging_id_tag

        CHARGER_VARIABLES.charging_id_tag = test_charging_id_tag

        expected_message = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": test_charging_id_tag,
                "meterStop": CHARGER_VARIABLES.meter_value_total,
                "timestamp": test_timestamp,
                "transactionId": test_transaction_id,
                "reason": "Remote",
                "transactionData": None  # [
                # {
                # Can place timestamp here. (Optional)
                # },
                # Can place meterValues here. (Optional)
                # ]
            }]

        #Act
        await websocket_instance.stop_transaction(test_is_remote)
        #Assert
        assert CHARGER_VARIABLES.status == "Available"
        assert message_sent is not None
        sent_message = json.loads(message_sent)
        assert sent_message[0] == expected_message[0]
        assert sent_message[1] == expected_message[1]
        assert sent_message[2] == expected_message[2]
        assert sent_message[3]["idTag"] == expected_message[3]["idTag"]
        assert sent_message[3]["meterStop"] == expected_message[3]["meterStop"]
        assert sent_message[3]["timestamp"] == pytest.approx(expected_message[3]["timestamp"],0.002)
        assert sent_message[3]["transactionId"] == expected_message[3]["transactionId"]
        assert sent_message[3]["reason"] == expected_message[3]["reason"]
        assert sent_message[3]["transactionData"] == expected_message[3]["transactionData"]
        #clan up
        CHARGER_VARIABLES.charging_id_tag = pre_test_charging_id

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_status, charger_is_charging, test_transaction_id",[
        ["Accepted",True,"1"],
        ["Rejected",False,"1"]
        ])
    async def test_remote_stop_transaction(self, test_status, charger_is_charging, test_transaction_id, websocket_instance):
        #Arrange
        pre_test_charger_is_charging = CHARGER_VARIABLES.is_charging

        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        was_remote = None
        async def mock_stop_transaction(is_remote):
            nonlocal was_remote
            was_remote = is_remote
            pass

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send
        websocket_instance.stop_transaction = mock_stop_transaction

        test_uuid = str(uuid.uuid4())

        test_message = [3, test_uuid, "RemoteStopTransaction", {"transactionID": test_transaction_id}]

        CHARGER_VARIABLES.is_charging = charger_is_charging
        
        msg = [3, test_uuid, "RemoteStopTransaction", {"status": test_status}]
        expected_message = json.dumps(msg)

        #Act
        await websocket_instance.remote_stop_transaction(test_message)
        
        #Assert
        assert message_sent is not None

        if not was_remote:
            assert was_remote is None

        assert message_sent == expected_message

        #Clean up
        CHARGER_VARIABLES.is_charging = pre_test_charger_is_charging
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_status, test_id_tag, test_reservation_id_tag",[
        ["Accepted", "12345", 12345],
        ["Rejected", "12345", 54321]
        ])
    async def test_remote_start_transaction(self, test_status, test_id_tag, test_reservation_id_tag, websocket_instance):
        #Arrange
        #save the global valuse for clean up
        pre_test_charger_status         = CHARGER_VARIABLES.status
        pre_test_charger_current_state  = CHARGER_VARIABLES.current_state
        pre_test_reservation_id_tag     = RESERVATION_VARIABLES.reservation_id_tag
        
        #messages
        test_uuid = str(uuid.uuid4())
        
        test_message = [3, test_uuid, "RemoteStartTransaction", {"idTag": test_id_tag}]
        
        msg = [3, test_uuid, "RemoteStartTransaction", {"status": test_status}]
        expected_message = json.dumps(msg)
        
        #intersepton funktions
        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        sent_message_status_notification = False
        async def mock_send_status_notification():
            nonlocal sent_message_status_notification
            sent_message_status_notification = True

        sent_message_start_transaktion = None
        async def mock_start_transaction(is_remote):
            nonlocal sent_message_start_transaktion
            sent_message_start_transaktion = is_remote
        
        #mock websocet
        websocket_instance._webSocket = mock.Mock()

        #assing the intersept funktions
        websocket_instance._webSocket.send = mock_send
        websocket_instance.start_transaction = mock_start_transaction
        websocket_instance.send_status_notification = mock_send_status_notification

        #set up reservation id
        RESERVATION_VARIABLES.reservation_id_tag = test_reservation_id_tag

        #Act
        await websocket_instance.remote_start_transaction(test_message)

        #Assert
        assert message_sent is not None
        assert message_sent == expected_message

        if(test_status == "Accepted"):
            assert sent_message_start_transaktion == True
            assert sent_message_status_notification == True
            assert CHARGER_VARIABLES.status == "Charging"
            assert CHARGER_VARIABLES.current_state == States.S_CHARGING
        else:
            assert sent_message_start_transaktion == None
            assert sent_message_status_notification == False
            assert CHARGER_VARIABLES.status != "Charging"
            assert CHARGER_VARIABLES.current_state != States.S_CHARGING

        #clean up
        CHARGER_VARIABLES.status                 = pre_test_charger_status
        CHARGER_VARIABLES.current_state          = pre_test_charger_current_state
        RESERVATION_VARIABLES.reservation_id_tag = pre_test_reservation_id_tag
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_status, test_local_reservation_id, test_reservation_id, test_reserved_connector, test_local_connector_id, test_expiry_date, test_id_tag",[
        ["Rejected", None, None, None, 0, 1234567890, "10111213"],
        ["Occupied", None, "12345", None, 0, 1234567890, "10111213"],
        ["Rejected", "12345", "12345", None, 0, 1234567890, "10111213"],
        ["Accepted", "12345", "12345", "67890", "67890", 1234567890, "10111213"],
        ["Accepted", "12345", None, "67890", "67890", 1234567890, "10111213"],
        ["Occupied", "54321", "12345", "67890", "67890", 1234567890, "10111213"]
    ])
    async def test_reserve_now(self, test_status, test_local_reservation_id, test_reserved_connector, test_reservation_id, test_local_connector_id, test_expiry_date, test_id_tag, websocket_instance):
        #Arrange
        #test_status = ["Rejected", "Accepted", "Occupied"]
        #test_reservation_id = [None,test_local_reservation_id]

        pre_test_charger_status         = CHARGER_VARIABLES.status
        pre_test_charger_state          = CHARGER_VARIABLES.current_state
        pre_test_is_reserved            = RESERVATION_VARIABLES.is_reserved
        pre_test_reservation_id         = RESERVATION_VARIABLES.reservation_id
        pre_test_reservation_id_tag     = RESERVATION_VARIABLES.reservation_id_tag
        pre_test_reservation_connector  = RESERVATION_VARIABLES.reserved_connector

        RESERVATION_VARIABLES.reservation_id = test_reservation_id
        RESERVATION_VARIABLES.reserved_connector =  test_reserved_connector
        
        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        sent_message_status_notification = False
        async def mock_send_status_notification():
            nonlocal sent_message_status_notification
            sent_message_status_notification = True

        hard_reset_reservation_trigerd = False
        async def mock_hard_reset_reservation():
            nonlocal hard_reset_reservation_trigerd
            hard_reset_reservation_trigerd = True

        websocket_instance._webSocket = mock.Mock()
        #interseption
        websocket_instance._webSocket.send = mock_send
        websocket_instance.hard_reset_reservation = mock_hard_reset_reservation
        websocket_instance.send_status_notification = mock_send_status_notification

        test_uuid = str(uuid.uuid4())
        
        test_message = [2,
               test_uuid,
               "ReserveNow",
               {
                "reservationID": test_local_reservation_id,
                "connectorID": test_local_connector_id,
                "expiryDate": test_expiry_date,
                "idTag": test_id_tag
                }]
        
        msg = [3, test_uuid, "ReserveNow", {"status": test_status}]
        expected_message = json.dumps(msg)
        #Act
        await websocket_instance.reserve_now(test_message)

        #Assert
        assert message_sent is not None

        if test_reservation_id == None or test_reservation_id == test_local_reservation_id:
            if test_reserved_connector == False and test_local_connector_id == 0:
                assert message_sent == expected_message
            
            else:
                assert hard_reset_reservation_trigerd == True
                assert RESERVATION_VARIABLES.is_reserved == True
                assert CHARGER_VARIABLES.status == "Reserved"
                assert sent_message_status_notification == True
                assert RESERVATION_VARIABLES.reservation_id_tag == int(test_id_tag)
                assert RESERVATION_VARIABLES.reservation_id == test_local_reservation_id
                assert RESERVATION_VARIABLES.reserved_connector == test_local_connector_id
                
                assert CHARGER_VARIABLES.current_state == States.S_FLEXICHARGEAPP
        
        elif test_reserved_connector == test_local_connector_id:
            assert message_sent == expected_message
        
        else:
            assert message_sent == expected_message

        #clean up
        CHARGER_VARIABLES.status                    = pre_test_charger_status
        CHARGER_VARIABLES.current_state             = pre_test_charger_state
        RESERVATION_VARIABLES.is_reserved           = pre_test_is_reserved
        RESERVATION_VARIABLES.reservation_id        = pre_test_reservation_id
        RESERVATION_VARIABLES.reservation_id_tag    = pre_test_reservation_id_tag
        RESERVATION_VARIABLES.reserved_connector    = pre_test_reservation_connector

    @pytest.mark.asyncio
    async def test_send_boot_notification_req(self, websocket_instance):
        """
        Test that the boot notification request is sent correctly
        """
        #Arrenge
        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send
        
        #Act
        await websocket_instance.send_boot_notification_req()
        
        #Assert
        assert message_sent is not None
        assert message_sent == '[2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "BootNotification", {"chargePointVendor": "AVT-Company", "chargePointModel": "AVT-Express", "chargePointSerialNumber": "avt.001.13.1", "chargeBoxSerialNumber": "avt.001.13.1.01", "firmwareVersion": "0.9.87", "iccid": "", "imsi": "", "meterType": "AVT NQC-ACDC", "meterSerialNumber": "avt.001.13.1.01"}]'
    
    @pytest.mark.asyncio
    async def test_send_boot_notification_conf(self, websocket_instance):
        #Arrange
        test_UUID = str(uuid.uuid4())
        
        test_msg = [2, test_UUID, "BootNotification", {
                    "chargePointVendor": "AVT-Company",
                    "chargePointModel": "AVT-Express",
                    "chargePointSerialNumber": "avt.001.13.1",
                    "chargeBoxSerialNumber": "avt.001.13.1.01",
                    "firmwareVersion": "0.9.87",
                    "iccid": "",
                    "imsi": "",
                    "meterType": "AVT NQC-ACDC",
                    "meterSerialNumber": "avt.001.13.1.01"}]

        msg = [3,
                    test_UUID,
                    "DataTransfer",
                    {"status": "Accepted"}]
        expected_message = json.dumps(msg)
        
        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        websocket_instance._webSocket = mock.Mock()
        websocket_instance._webSocket.send = mock_send
        
        #Act
        await websocket_instance.send_boot_notification_conf(test_msg)
        
        #Assert
        assert message_sent is not None
        assert message_sent == expected_message
    
    @pytest.mark.skip("Not Implemented in code base")
    @pytest.mark.asyncio
    async def test_start_charging_from_reservation(self):
        #Arrange
        #Act
        #Assert
        pass
    
    @pytest.mark.skip("Not Implemented in code base")
    @pytest.mark.asyncio
    async def test_hard_reset_charging(self):
        #Arrange
        #Act
        #Assert
        pass
    
    @pytest.mark.skip("Not Implemented in code base")
    @pytest.mark.asyncio
    async def test_hard_reset_reservation(self):
        #Arrange
        #Act
        #Assert
        pass
    
    @pytest.mark.skip("Not Implemented in code base")
    @pytest.mark.asyncio
    async def test_send_periodic_meter_values(self):
        #Arrange
        #Act
        #Assert
        pass
    
    @pytest.mark.asyncio
    async def test_send_heartbeat(self,websocket_instance):
        #Arrange
        message_sent = None
        async def mock_send(message):
            nonlocal message_sent
            message_sent = message

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "Heartbeat", {}]
        expected_message = json.dumps(msg)

        websocket_instance._webSocket = mock.Mock()
        #interseption
        websocket_instance._webSocket.send = mock_send
        #Act
        await websocket_instance.send_heartbeat()

        #Assert
        assert message_sent is not None
        assert message_sent == expected_message
    
    @pytest.mark.skip("Not working in code base")
    @pytest.mark.asyncio
    async def test_check_if_time_for_heartbeat(self):
        #Arrange
        #Act
        #Assert
        pass
    
    @pytest.mark.asyncio
    async def test_send_meter_values(self, websocket_instance):
        #Arrange
        pre_test_charger_id             = CHARGER_VARIABLES.charger_id
        pre_test_charging_W             = CHARGER_VARIABLES.charging_W
        pre_test_current_charge_percent = CHARGER_VARIABLES.current_charging_percentage

        assert CHARGER_VARIABLES.meter_value_total == 0

        timestamp = int(time.time() * 1000)
        unique_id = str(CHARGER_VARIABLES.charger_id) + "MeterValues" + str(timestamp)

        sent_message = None
        async def mock_send_message(message):
            nonlocal sent_message
            sent_message = message

        websocket_instance.send_message = mock_send_message

        expected_message = [2,
                unique_id,
                "MeterValues",
                {
                    "connectorId": 1,
                    "transactionId": 1,
                    "timestamp": timestamp,
                    "values": {
                        "chargingPercent": {
                            "value": CHARGER_VARIABLES.current_charging_percentage,
                            "unit": "%",
                            "measurand": "SoC"

                        },
                        "chargingPower": {
                            "value": CHARGER_VARIABLES.charging_W,
                            "unit": "W",
                            "measurand": "Power.Active,Import"
                        },
                        "chargedSoFar": {
                            "value": CHARGER_VARIABLES.meter_value_total,
                            "unit": "Wh",
                            "measurand": "Energy.Active.Import"
                        }

                    }
                }]
        
        #Act
        await websocket_instance.send_meter_values()

        #Assert
        assert sent_message is not None
        sent_message = json.loads(sent_message)

        assert sent_message[0]                                           == expected_message[0]
        assert sent_message[1]                                           == expected_message[1]
        assert sent_message[2]                                           == expected_message[2]
        assert sent_message[3]["connectorId"]                            == expected_message[3]["connectorId"]
        assert sent_message[3]["transactionId"]                          == expected_message[3]["transactionId"]
        assert sent_message[3]["timestamp"]                              == pytest.approx(expected_message[3]["timestamp"],2)
        assert sent_message[3]["values"]["chargingPercent"]["value"]     == expected_message[3]["values"]["chargingPercent"]["value"]
        assert sent_message[3]["values"]["chargingPercent"]["unit"]      == expected_message[3]["values"]["chargingPercent"]["unit"]
        assert sent_message[3]["values"]["chargingPercent"]["measurand"] == expected_message[3]["values"]["chargingPercent"]["measurand"]
        assert sent_message[3]["values"]["chargingPower"]["value"]       == expected_message[3]["values"]["chargingPower"]["value"]
        assert sent_message[3]["values"]["chargingPower"]["unit"]        == expected_message[3]["values"]["chargingPower"]["unit"]
        assert sent_message[3]["values"]["chargingPower"]["measurand"]   == expected_message[3]["values"]["chargingPower"]["measurand"]
        assert sent_message[3]["values"]["chargedSoFar"]["value"]        == expected_message[3]["values"]["chargedSoFar"]["value"]
        assert sent_message[3]["values"]["chargedSoFar"]["unit"]         == expected_message[3]["values"]["chargedSoFar"]["unit"]
        assert sent_message[3]["values"]["chargedSoFar"]["measurand"]    == expected_message[3]["values"]["chargedSoFar"]["measurand"]

        #clean up
        CHARGER_VARIABLES.charger_id = pre_test_charger_id
        CHARGER_VARIABLES.charging_W = pre_test_charging_W
        CHARGER_VARIABLES.current_charging_percentage = pre_test_current_charge_percent

    @pytest.mark.asyncio
    async def test_send_data_reserve(self, websocket_instance):
        #Arrange
        sent_message = None
        async def mock_send_message(message):
            nonlocal sent_message
            sent_message = message

        websocket_instance.send_message = mock_send_message

        msg = ["chargerplus", "ReserveNow"]
        expected_message = json.dumps(msg)
        #Act
        await websocket_instance.send_data_reserve()

        #Assert
        assert sent_message is not None
        assert sent_message == expected_message
    
    @pytest.mark.asyncio
    async def test_send_data_remote_start(self, websocket_instance):
        #Arrange
        sent_message = None
        async def mock_send_message(message):
            nonlocal sent_message
            sent_message = message

        websocket_instance.send_message = mock_send_message

        msg = ["chargerplus", "RemoteStart"]
        expected_message = json.dumps(msg)
        #Act
        await websocket_instance.send_data_remote_start()

        #Assert
        assert sent_message is not None
        assert sent_message == expected_message
    
    @pytest.mark.asyncio
    async def test_send_data_remote_stop(self, websocket_instance):
        #Arrange
        sent_message = None
        async def mock_send_message(message):
            nonlocal sent_message
            sent_message = message

        websocket_instance.send_message = mock_send_message

        msg = ["chargerplus", "RemoteStop"]
        expected_message = json.dumps(msg)
        #Act
        await websocket_instance.send_data_remote_stop()

        #Assert
        assert sent_message is not None
        assert sent_message == expected_message