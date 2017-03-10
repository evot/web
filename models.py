import json

from utils import log


def save(data, path):
    s = json.dumps(data, indent=2, ensure_ascii=False)
    with open(path, 'w+', encoding='utf-8') as f:
        # log('save', path, s, data)
        f.write(s)


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        s = f.read()
        # log('load', s)
        return json.loads(s)


class Model(object):
    @classmethod
    def db_path(cls):
        classname = cls.__name__
        path = 'dbfiles/{}.txt'.format(classname)
        return path

    @classmethod
    def all(cls):
        path = cls.db_path()
        models = load(path)
        ms = [cls(m) for m in models]
        return ms

    @classmethod
    def find_all(cls, **kwargs):
        ms = []
        log('kwargs, ', kwargs, type(kwargs))
        k, v = '', ''
        for key, value in kwargs.items():
            k, v = key, value
        all = cls.all()
        for m in all:
            # getattr(m, k)
            if v == m.__dict__[k]:
                ms.append(m)
        return ms

    @classmethod
    def find_by(cls, **kwargs):
        log('kwargs, ', kwargs, type(kwargs))
        k, v = '', ''
        for key, value in kwargs.items():
            k, v = key, value
        all = cls.all()
        for m in all:
            if v == m.__dict__[k]:
                return m
        return None

    @classmethod
    def find(cls, id):
        return cls.find_by(id=id)

    @classmethod
    def delete(cls, id):
        models = cls.all()
        index = -1
        for i, e in enumerate(models):
            if e.id == id:
                index = i
                break
        if index == -1:
            pass
        else:
            models.pop(index)
            l = [m.__dict__ for m in models]
            path = cls.db_path()
            save(l, path)
            return

    def __repr__(self):
        classname = self.__class__.__name__
        properties = ['{}: ({})'.format(k, v) for k, v in self.__dict__.items()]
        s = '\n'.join(properties)
        return '< {}\n{} \n>\n'.format(classname, s)

    def save(self):
        models = self.all()
        if self.id is None:
            if len(models) == 0:
                self.id = 1
            else:
                m = models[-1]
                # log('m', m)
                self.id = m.id + 1
            models.append(self)
        else:
            # index = self.find(self.id)
            index = -1
            for i, m in enumerate(models):
                if m.id == self.id:
                    index = i
                    break
            log('debug', index)
            models[index] = self
        l = [m.__dict__ for m in models]
        path = self.db_path()
        save(l, path)


class User(Model):
    def __init__(self, form):
        self.id = form.get('id', None)
        self.username = form.get('username', '')
        pwd = form.get('password', '')
        self.password = pwd

    def sha1_password(self, pwd):
        import hashlib
        s = hashlib.sha1(pwd.encode('ascii'))
        return s.hexdigest()

    def validate_login(self):
        u = User.find_by(username=self.username)
        log('valid login', u, self)
        if u is not None:
            pwd = self.sha1_password(self.password)
            log('compare pwd', pwd, u.password == pwd)
            return u.password == pwd
        else:
            return False

    def validate_register(self):
        valid = len(self.username) > 2
        if valid:
            self.password = self.sha1_password(self.password)
        return valid

    def todos(self):
        ts = []
        for t in Todo.all():
            if t.user_id == self.id:
                ts.append(t)
        return ts


class Todo(Model):
    @classmethod
    def new(cls, form, user_id=-1):
        t = cls(form, user_id)
        t.save()
        return t

    @classmethod
    def update(cls, id, form):
        t = cls.find(id)
        valid_names = [
            'task',
            'completed'
        ]
        for key in form:
            if key in valid_names:
                setattr(t, key, form[key])
        t.save()

    @classmethod
    def complete(cls, id, completed):
        t = cls.find(id)
        t.completed = completed
        t.save()
        return t

    def is_owner(self, id):
        return self.user_id == id

    def __init__(self, form, user_id=-1):
        self.id = form.get('id', None)
        self.task = form.get('task', '')
        self.completed = False
        self.user_id = form.get('user_id', user_id)
