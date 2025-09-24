const db = require('./db');
const bcrypt = require('bcryptjs');

const User = {};

User.create = async (username, email, password) => {
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    // This is a simplified example. In a real application, you would use transactions
    // to ensure that both the user and the identity are created successfully.
    const userResult = await db.query(
        'INSERT INTO users (username, email) VALUES ($1, $2) RETURNING id',
        [username, email]
    );
    const userId = userResult.rows[0].id;

    await db.query(
        'INSERT INTO user_identities (provider, provider_uid, user_id) VALUES ($1, $2, $3)',
        ['local', hashedPassword, userId]
    );

    return { id: userId, username, email };
};

User.findByEmail = async (email) => {
    const { rows } = await db.query('SELECT * FROM users WHERE email = $1', [email]);
    if (rows.length === 0) {
        return null;
    }
    const user = rows[0];

    // Get password hash from user_identities
    const identityResult = await db.query(
        'SELECT provider_uid FROM user_identities WHERE user_id = $1 AND provider = $2',
        [user.id, 'local']
    );

    if (identityResult.rows.length > 0) {
        user.password = identityResult.rows[0].provider_uid;
    }

    return user;
};

module.exports = User;
