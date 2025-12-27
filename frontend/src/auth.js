import { CognitoUserPool, CognitoUser, AuthenticationDetails } from 'amazon-cognito-identity-js';

// Configuração com os SEUS IDs
const poolData = {
  UserPoolId: 'us-east-1_wb0k4NVxn',       // <-- Seu ID
  ClientId: '6cncs143qbbqg0haas8ot89042'    // <-- Seu Client ID
};

const userPool = new CognitoUserPool(poolData);

export const getSession = () => {
  return new Promise((resolve, reject) => {
    const user = userPool.getCurrentUser();
    if (!user) {
      reject("Nenhum usuário logado");
      return;
    }

    user.getSession((err, session) => {
      if (err) {
        reject(err);
        return;
      }
      resolve(session);
    });
  });
};

export const logout = () => {
  const user = userPool.getCurrentUser();
  if (user) user.signOut();
  window.location.reload(); // Recarrega para limpar estados
};

export const login = (email, password) => {
  return new Promise((resolve, reject) => {
    const authDetails = new AuthenticationDetails({
      Username: email,
      Password: password
    });

    const user = new CognitoUser({
      Username: email,
      Pool: userPool
    });

    user.authenticateUser(authDetails, {
      onSuccess: (data) => {
        resolve(data);
      },
      onFailure: (err) => {
        reject(err);
      },
      newPasswordRequired: (userAttributes, requiredAttributes) => {
        // Se a AWS pedir troca de senha no primeiro acesso
        // Vamos forçar a mesma senha para simplificar este tutorial
        // Em um app real, abriríamos um modal pedindo nova senha
        user.completeNewPasswordChallenge(password, {}, {
            onSuccess: resolve,
            onFailure: reject
        });
      }
    });
  });
};

export const getToken = async () => {
    try {
        const session = await getSession();
        return session.getIdToken().getJwtToken();
    } catch (e) {
        return null;
    }
}