$:.unshift(File.dirname(__FILE__))

require 'test_helper'

class MqttSnPubTest < Minitest::Test

  def test_publish_qos_n1
    fake_server do |fs|
      @packet = fs.wait_for_packet(MQTT::SN::Packet::Publish) do
        @cmd_result = run_cmd(
          'mqtt-sn-pub-cov',
          '-q' => -1,
          '-T' => 10,
          '-m' => 'test_publish_qos_n1',
          '-p' => fs.port,
          '-h' => fs.address
        )
      end
    end

    assert_empty(@cmd_result)
    assert_equal(10, @packet.topic_id)
    assert_equal(:predefined, @packet.topic_id_type)
    assert_equal('test_publish_qos_n1', @packet.data)
    assert_equal(-1, @packet.qos)
    assert_equal(false, @packet.retain)
    assert_equal(0, @packet.id)
  end
end