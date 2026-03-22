import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';
import * as Notifications from 'expo-notifications';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export default function App() {
  const sendLocalNotification = async () => {
    const { status } = await Notifications.getPermissionsAsync();
    let finalStatus = status;
    
    if (status !== 'granted') {
      const { status: newStatus } = await Notifications.requestPermissionsAsync();
      finalStatus = newStatus;
    }
    
    if (finalStatus !== 'granted') {
      alert('需要通知权限！');
      return;
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title: '📢 通知',
        body: 'Hello World!',
        sound: true,
      },
      trigger: {
        type: 'timeInterval',
        seconds: 1,
      },
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Hello World</Text>
      
      <TouchableOpacity style={styles.button} onPress={sendLocalNotification}>
        <Text style={styles.buttonText}>推送消息</Text>
      </TouchableOpacity>
      
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 40,
    color: '#333',
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});
