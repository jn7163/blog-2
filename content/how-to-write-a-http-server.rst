How To Write A HTTP Server
--------------------------

:date: 2013-12-12 01:22
:tags: tech
:category: Tech
:slug: how-to-write-a-http-server
:author: `Y. T. Chung`

Today I am going to write a HTTP server from scratch. I write this in order to practice my programming skills and check my understanding of UNIX network programming. It will be written in C++11, the new C++ standard.

Architecture
============

I am going to write an HTTP server running on single thread. I will take example by Tornado_, a famous HTTP network framework created by Facebook_.

.. _Tornado: http://www.tornadoweb.org/
.. _Facebook: http://www.facebook.com/

The whole server consists of **four** layers: **Connection Layer**, **Stream Layer**, **HTTP Connection Layer**, **Application Layer**.

+--------------------------------+--------------------------------------------------------------------+
|   Application Layer            |  The Topest layer for implementing server-side logic.              |
+--------------------------------+--------------------------------------------------------------------+
|   HTTP Connection Layer        |  Processing HTTP packet.                                           |
+--------------------------------+--------------------------------------------------------------------+
|   Stream Layer                 |  For buffering input/output data and pack/unpack application data. |
+--------------------------------+--------------------------------------------------------------------+
|   Connection Layer             |  Sockets and I/O multiplexer. Accepting connections from clients.  |
+--------------------------------+--------------------------------------------------------------------+

The **Connection Layer** accepts connections from clients and uses a I/O multiplexer to manage all sockets. We can set callback functons in the connection layer. So when the sockets' buffer have data to receive or have space for sending data, it will inform the callback functions. We don not have to write a loop to ask for data, just wait for the signal.

The **Stream Layer** get the information from the **Connection Layer** and then read/write data from its buffer. There is a stream object for each client.

The **HTTP Connection Layer** exacts HTTP header and body from the stream layer's buffer and gets data from **Application Layer** to build a HTTP packet.

The **Application Layer** is for implementing server-side logic. In this layer, all data that comes from clients will become a C++ object. You can access every part of data directly and you do not need to worry about how the data will be sent and received.

Let's start!
============

Connection Layer
################

**Connection Layer** is consists of two models: **TcpSocket** and **IOLoop**. Let's have a brief look at their declaration.

Sockets
```````

.. code:: cpp

    #include <sys/socket.h>
    #include <sys/types.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <memory>
    #include <stdexcept>

    namespace httpserver {
        class SocketError : public std::runtime_error {
            public:
                explicit SocketError(int fd, int code, const std::string& msg);
                explicit SocketError(int fd, int code, const char *msg);
                int code() const;
                int fd() const;
            private:
                int _code;
                int _fd;
        };

        class SocketClient {
            public:
                SocketClient(int cfd, const struct sockaddr_in& addr, bool nonblock = true);

                ~SocketClient();

                SocketClient(const SocketClient& rhs);
                SocketClient(SocketClient&& rhs);

                /**
                 * Send data to the client
                 * @param buf a pointer to the buffer
                 * @param len number of bytes to send
                 * @throw SocketError
                 * @return number of bytes that sent
                 */
                int send(const char *buf, int len) throw (SocketError);

                /**
                 * Receive data from the client
                 * @param buf a pointer to the buffer
                 * @param buffer size
                 * @throw SocketError
                 * @return number of bytes that received
                 */
                int recv(char *buf, int len) throw (SocketError);

                const char *ip_address() const;
                int fd() const;
                uint16_t port() const;

                /**
                 * Close the file discriptor
                 */
                void close();
                /**
                 * Shutdown the socket
                 * @param how SHUT_RD or SHUT_WR or SHUT_RDWR
                 */
                void shutdown(int how = SHUT_RD);
            private:
                int cfd;                 // File discriptor of the socket
                struct sockaddr_in addr; // Socket address information
        };

        class TcpServer {
            public:
                /**
                 * Construct a socket server
                 * @param port port to listen
                 * @param queuelen listen queue len
                 * @param nonblock set non-blocking mode or not
                 */
                TcpServer(uint16_t port = 8000,
                          unsigned int queuelen = 5,
                          bool nonblock = true);

                ~TcpServer();

                TcpServer(const TcpServer&) = delete;
                TcpServer& operator=(const TcpServer&) = delete;
                int fd() const;

                /**
                 * Accept the connection from client
                 * @throw SocketError
                 * @return SocketClient for the client
                 */
                SocketClient accept() throw (SocketError);

                /**
                 * Close the file discriptor
                 */
                void close();
                /**
                 * Shutdown the socket
                 * @param how SHUT_RD or SHUT_WR or SHUT_RDWR
                 */
                void shutdown(int how = SHUT_RD);
            private:
                int sfd;                  // File discriptor of the socket
                struct sockaddr_in addr;  // Socket address information
                bool is_nonblock;
        };
    }

You can see the ``SocketClient`` and ``TcpServer`` classes are wrappers of sockets. So the definition of them are very easy to write. I will show you some of them here.

.. code:: cpp

    SocketClient::SocketClient(int cfd, const struct sockaddr_in& addr, bool nonblock)
        : cfd(cfd), addr(addr) {

        // Set the socket to non-blocking mode
        if (nonblock) {
            int opts;
            if ((opts = fcntl(cfd, F_GETFL)) < 0) {
                perror("fcntl");
                std::abort();
            }

            opts = (opts | O_NONBLOCK);
            if (fcntl(cfd, F_SETFL, opts) < 0) {
                perror("fcntl");
                std::abort();
            }
        }
    }

    int SocketClient::send(const char *buf, int len) throw (SocketError) {
        int ret = ::send(cfd, buf, len, 0);

        if (ret <= 0) {
            throw SocketError(cfd, errno, strerror(errno));
        }
        else if (ret == 0) {
            throw SocketError(cfd, EREMOTEIO, "remote client closed");
        }
        return ret;
    }

    int SocketClient::recv(char *buf, int len) throw (SocketError) {
        int ret = ::recv(cfd, buf, len, 0);
        if (ret <= 0) {
            throw SocketError(cfd, errno, strerror(errno));
        }
        else if (ret == 0) {
            throw SocketError(cfd, EREMOTEIO, "remote client closed");
        }
        return ret;
    }

    TcpServer::TcpServer(uint16_t port, unsigned int queuelen, bool nonblock)
        : is_nonblock(nonblock) {
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = INADDR_ANY;
        addr.sin_port = htons(port);

        // Create a socket
        if ((sfd = socket(PF_INET, SOCK_STREAM, 0)) < 0) {
            perror("socket");
            std::abort();
        }

        int opt = 1;
        // Set the SO_REUSEADDR option
        setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
        if (bind(sfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
            perror("bind");
            std::abort();
        }

        // set non-blocking mode
        if (is_nonblock) {
            if ((opt = fcntl(sfd, F_GETFL)) < 0) {
                perror("fcntl");
                std::abort();
            }

            opt = (opt | O_NONBLOCK);
            if (fcntl(sfd, F_SETFL, opt) < 0) {
                perror("fcntl");
                std::abort();
            }
        }

        listen(sfd, queuelen);
    }

    SocketClient TcpServer::accept() throw (SocketError) {
        int cfd;
        struct sockaddr_in remoteaddr;
        socklen_t sin_size = sizeof(struct sockaddr_in);
        if ((cfd = ::accept(sfd, (struct sockaddr *)&remoteaddr, &sin_size)) < 0) {
            throw SocketError(sfd, errno, strerror(errno));
        }

        return SocketClient(cfd, remoteaddr, is_nonblock);
    }

IOLoop
``````

**IOLoop** is the I/O multiplexer. We can write a base class ``IOLoop`` and then implement a specific IOLoop for each platform (EPoll on Linux and KQueue on BSD).

.. code:: cpp

    class IOLoop {
        public:
            IOLoop();
            virtual ~IOLoop();

            enum EventType {
                EV_READ = 0x0001,
                EV_WRITE = 0x0002,
                EV_ERROR = 0x0004
            };

            typedef std::function<void (int, int, void *, IOLoop&)> EventCallback;

            /**
             * Add a handler for `fd`
             * @param fd file discriptor
             * @param event events to listen.
             * @param callback callback function
             * @param arg a pointer to a argument that you want to pass to the callback
             * @throw IOLoopException
             */
            virtual void add_handler(int fd,
                                     int event,
                                     const EventCallback& callback,
                                     void *arg = nullptr) throw (IOLoopException);
            /**
             * Update the handler for `fd`
             * @param fd file discriptor
             * @param event events to listen
             * @throw IOLoopException
             */
            virtual void update_handler(int fd, int event) throw (IOLoopException) = 0;
            /**
             * Remove handler
             * @param fd file discriptor
             * @throw IOLoopException
             */
            virtual void remove_handler(int fd) throw (IOLoopException);

            /**
             * Start the loop
             */
            virtual int start() throw (IOLoopException);
            /**
             * Stop the loop
             */
            virtual void stop() throw (IOLoopException);

        protected:
            void toggle_callback(int fd, int type);

            struct IOEvent {
                int fd;
                EventCallback callback;
                void *arg;

                IOEvent();
                IOEvent(int, EventCallback, void *);
            };

        private:
            std::unordered_map<int, IOEvent> handlers;
            bool started;
    };

Three member functions: ``add_handler``, ``update_handler`` and ``remove_handler`` have to be implemented in ``IOLoop``'s subclasses. But the ``IOLoop::add_handler`` and ``IOLoop::remove_handler`` are for storing ``IOEvent`` objects in the data member ``handlers``, so subclasses have to call the ``IOLoop::add_handler`` and ``IOLoop::remove_handler`` in their own ``add_handler`` and ``remove_handler``.

Let's see the code of ``IOLoop::add_handler`` and ``IOLoop::remove_handler``:

.. code:: cpp

    void IOLoop::add_handler(int fd,
                             int event,
                             const EventCallback& callback,
                             void *arg) throw (IOLoopException) {
        handlers[fd] = IOEvent(fd, callback, arg);
    }

    void IOLoop::remove_handler(int fd) throw (IOLoopException) {
        auto iter = handlers.find(fd);
        if (iter != handlers.end())
            handlers.erase(iter);
        else
            throw IOLoopException("Handler not exists");
    }

``IOLoop`` is a abstract class, so we have to write a subclass of ``IOLoop``. Here I will take ``EPollIOLoop`` as an example. ``EPollIOLoop`` implements a epoll I/O multiplexer in it. Here is the code.

.. code:: cpp

    class EPollIOLoop : public IOLoop {
        public:
        // Member functions here

        private:
            int epoll_fd;

            static const size_t EPOLL_MAX_EVENT = 1024;
            std::array<struct epoll_event, EPOLL_MAX_EVENT> events;

            int wake_pipe[2]; // A Pipe for stopping the loop.
                              // Because if no event occur, the loop will stop and wait for events
                              // we have to wake the epoll loop and exit it.
    };

    EPollIOLoop::EPollIOLoop(int argc, char **argv)
        : IOLoop(argc, argv) {
        if ((epoll_fd = epoll_create(EPOLL_MAX_EVENT)) < 0) {
            perror("epoll_create");
            exit(EXIT_FAILURE);
        }

        // This is the pipe for waking the loop.
        if (pipe(wake_pipe) < 0) {
            perror("pipe");
            exit(EXIT_FAILURE);
        }

        struct epoll_event ev;
        ev.events = EPOLLIN | EPOLLET;
        ev.data.fd = wake_pipe[0];
        if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, wake_pipe[0], &ev)) {
            perror("epoll_ctl");
            exit(EXIT_FAILURE);
        }
    }

    void EPollIOLoop::add_handler(int fd,
                                  int type,
                                  const EventCallback& callback,
                                  void *arg) throw (IOLoopException) {
        struct epoll_event epev;
        memset(&epev, 0, sizeof(epev));

        // Choose the event type to listen
        if (type & EV_READ) epev.events |= EPOLLIN;
        if (type & EV_WRITE) epev.events |= EPOLLOUT;

        epev.events |= (EPOLLERR | EPOLLHUP | EPOLLRDHUP | EPOLLET);

        epev.data.fd = fd;

        if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &epev)) {
            perror("epoll_ctl");
            throw IOLoopException("EPoll add error");
        }

        // Have to be called!!
        IOLoop::add_handler(fd, type, callback, arg);
    }

    void EPollIOLoop::update_handler(int fd, int type) throw (IOLoopException) {
        struct epoll_event epev;
        memset(&epev, 0, sizeof(epev));

        if (type & EV_READ) epev.events |= EPOLLIN;
        if (type & EV_WRITE) epev.events |= EPOLLOUT;

        epev.events |= (EPOLLERR | EPOLLHUP | EPOLLRDHUP | EPOLLET);

        epev.data.fd = fd;

        if (epoll_ctl(epoll_fd, EPOLL_CTL_MOD, fd, &epev)) {
            perror("epoll_ctl");
            throw IOLoopException("EPoll add error");
        }
    }

    // Just remove the fd from epoll
    void EPollIOLoop::remove_handler(int fd) throw (IOLoopException) {
        if (epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, nullptr)) {
            perror("epoll_ctl");
            throw IOLoopException("EPoll del error");
        }

        IOLoop::remove_handler(fd);
    }

    // The event loop
    int EPollIOLoop::start() throw (IOLoopException) {
        IOLoop::start();
        int n;
        while ((n = epoll_wait(epoll_fd, events.data(), events.max_size(), -1)) >= 0) {
            for (int i = 0; i < n; ++ i) {
                int type = 0;

                if (events[i].data.fd == wake_pipe[0])
                    goto FINISHED;

                if (events[i].events & EPOLLIN)
                    type |= EV_READ;

                if (events[i].events & EPOLLOUT)
                    type |= EV_WRITE;

                if (events[i].events & (EPOLLERR | EPOLLHUP | EPOLLRDHUP))
                    type |= EV_ERROR;

                try {
                    toggle_callback(events[i].data.fd, type);
                }
                catch (std::exception& except) {
                    std::cerr << __FILE__ << ":" << __LINE__ << " "
                        << except.what() << std::endl;
                    goto FAILED;
                }
            }
        }

    FINISHED:
        return EXIT_SUCCESS;
    FAILED:
        return EXIT_FAILURE;
    }

    // Send a "x" to the pipe to wake up the loop
    void EPollIOLoop::stop() throw (IOLoopException) {
        char buf[] = "x";
        write(wake_pipe[1], buf, sizeof(buf));
    }

Stream Layer
############

**Stream Layer** is for buffering data for read and write. It will try to read or write as much as data as it can when the it is allowed. If the socket is set to non-blocking mode, you will get an ``EAGAIN`` error if there is nothing to read or there is no enough space for writing. With the help of I/O multiplexer, we can read and write sockets asynchronously. Let's see the declaration of ``IOStream``:

.. code:: cpp

    class IOStream {
        public:
            IOStream(const SocketClient& client, IOLoop& ioloop);
            ~IOStream();

            typedef std::function<void (const std::string& data, IOStream& stream)> ReadHandler;
            typedef std::function<void (IOStream& stream)> WriteHandler;

            /**
             * Read bytes. It will call the handler when it is done.
             * @param len number of bytes
             * @param handler callback
             */
            void read_bytes(size_t len, const ReadHandler& handler = ReadHandler());
            /**
             * Read bytes until a we meet a specific substring. It will call the handler when it is done.
             * @param until the specific substring
             * @param handler callback
             */
            void read_until(const char *until, const ReadHandler& handler = ReadHandler());

            /**
             * Write bytes. It will call the handler when it is done.
             * @param buffer a pointer to the buffer
             * @param len number of bytes to write
             * @handler callback
             */
            void write_bytes(const void *buffer, size_t len, const WriteHandler& handler = WriteHandler());

            SocketClient client() const;
            void set_close_callback(const std::function<void (IOStream *)>&);
            void close();
        private:
            // The callback that set in IOLoop
            void __handler_poll(int fd, int type, void *arg, IOLoop& loop);

            size_t __read_to_buffer(SocketClient *client) throw (IOStreamException);
            bool __read_from_buffer();

            SocketClient _client;
            IOLoop& ioloop;
            bool _doing;
            bool _write_buf_freezing;
            int _read_num;
            const char *_read_until;
            ReadHandler _read_handler;
            WriteHandler _write_handler;

            std::function<void (IOStream *)> _close_callback;

            int _send_buf_size;
            int _recv_buf_size;
            char *_send_buf;
            char *_recv_buf;
            std::deque<char> _rdbuf;
            std::deque<char> _wrbuf;

            bool _closed;
    };

So much data members, ahh... But we only need to focus on some of them.

The ``_rdbuf`` is the read buffer and the ``_wrbuf`` is the write buffer. These two buffer store data for transfering to the upper layer and the data comes from the upper layer.

The ``_send_buf`` is the write buffer for writing data from socket client and the ``_recv_buf`` is the read buffer for reading data from socket client.

Let's see how to implement some of the member functions.

.. code:: cpp

    IOStream::IOStream(const SocketClient& client, IOLoop& loop)
        : _client(client), ioloop(loop), _doing(false), _write_buf_freezing(false),
          _read_num(-1), _read_until(nullptr), _closed(false) {

        ioloop.add_handler(_client.fd(), IOLoop::EV_READ | IOLoop::EV_WRITE,
                [this] (int fd, int type, void *arg, IOLoop& loop)
                    { __handler_poll(fd, type, arg, loop); }, &_client);

        // Get the size of socket send and recv buffer size.
        unsigned int _sz = sizeof(_send_buf_size);
        if (getsockopt(_client.fd(), SOL_SOCKET, SO_SNDBUF, &_send_buf_size, &_sz)) {
            perror("getsockopt");
            std::abort();
        }
        if (getsockopt(_client.fd(), SOL_SOCKET, SO_RCVBUF, &_recv_buf_size, &_sz)) {
            perror("getsockopt");
            std::abort();
        }

        _send_buf = new char[_send_buf_size];
        _recv_buf = new char[_recv_buf_size];
    }

    void IOStream::read_bytes(size_t len, const ReadHandler& handler) {
        if (len == 0 || _closed) {
            handler("", *this);
            return;
        }

        _read_num = len;
        _read_handler = handler;
        while (true) {
            // If the data in _rdbuf is enough, return it
            if (this->__read_from_buffer()) break;
            try {
                // Try to get some data from socket
                if (this->__read_to_buffer(&_client) == 0) break;
            }
            catch (const IOStreamException& except) {
                this->close();
                break;
            }
        }
    }

    void IOStream::read_until(const char *until, const ReadHandler& handler) {
        if (!until || _closed) return;

        _read_until = until;
        _read_handler = handler;

        while (true) {
            // If the data in _rdbuf is enough, return it
            if (this->__read_from_buffer()) break;
            try {
                // Try to get some data from socket
                if (this->__read_to_buffer(&_client) == 0) break;
            }
            catch (const IOStreamException& except) {
                this->close();
                break;
            }
        }
    }

    void IOStream::write_bytes(const void *buffer, size_t len, const WriteHandler& handler) {
        if (!buffer || len == 0 || _closed) return;

        const char *_buf = static_cast<const char *>(buffer);
        // Just copy it to the _wrbuf
        std::copy(_buf, _buf + len, back_inserter(_wrbuf));

        ioloop.update_handler(_client.fd(), IOLoop::EV_READ | IOLoop::EV_WRITE);

        _write_handler = handler;
    }

    // The callback of IOLoop
    void IOStream::__handler_poll(int fd, int type, void *arg, IOLoop& loop) {
        SocketClient *clientSocket = static_cast<SocketClient *>(arg);

        if (type & IOLoop::EV_READ) {
            //std::lock_guard<std::mutex> lck(this->_rdmutex);
            size_t result = 0;
            try {
                // Read data to the _rdbuf
                result = this->__read_to_buffer(clientSocket);
            }
            catch (const IOStreamException& except) {
                goto ERROR_OCCUR;
            }

            if (result != 0) {
                this->__read_from_buffer();
            }
        }

        if (type & IOLoop::EV_WRITE) {
            size_t n_avail = _wrbuf.size();
            if (n_avail > 0) {
                // Write as much data as possible
                while (!_wrbuf.empty()) {

                    int total = (_wrbuf.size() < _send_buf_size) ? _wrbuf.size() : _send_buf_size;

                    auto _wrbuf_iter = _wrbuf.begin();
                    auto _end_iter = _wrbuf_iter + total;
                    int index = 0;
                    while (_wrbuf_iter != _end_iter) _send_buf[index ++] = *(_wrbuf_iter ++);

                    try {
                        total = clientSocket->send(_send_buf, total);
                    }
                    catch (SocketError& except) {
                        if (except.code() == EAGAIN || except.code() == EWOULDBLOCK) {
                            // Socket buffer full
                            break;
                        }
                        else {
                            std::cerr << "Socket send error: " << except.what() << std::endl;
                            goto ERROR_OCCUR;
                        }
                    }

                    while (total --) _wrbuf.pop_front();

                }

                if (_write_handler) {
                    auto h = _write_handler;
                    _write_handler = WriteHandler();
                    h(*this);
                }
            }
        }

        if (type & IOLoop::EV_ERROR) {
            goto ERROR_OCCUR;
        }
        return;
    ERROR_OCCUR:
        this->close();
    }

    // Read data from socket to _rdbuf
    size_t IOStream::__read_to_buffer(SocketClient *client) throw (IOStreamException) {
        size_t readsize = 0;
        while (true) {
            int n = 0;
            try {
                n = client->recv(_recv_buf, _recv_buf_size);
                readsize += n;
                std::copy(_recv_buf, _recv_buf + n, back_inserter(_rdbuf));
            }
            catch (SocketError& except) {
                if (except.code() == EAGAIN || except.code() == EWOULDBLOCK) break;
                else {
                    std::cerr << __FILE__ << ":" << __LINE__ << " " << except.fd() << " " << except.what() << std::endl;
                    throw IOStreamException(except.what());
                }
            }
        }
        return readsize;
    }

    bool IOStream::__read_from_buffer() {
        // Read bytes
        if (_read_num != -1) {
            if (_rdbuf.size() >= _read_num && _rdbuf.size() != 0) {
                int _remain = _read_num;
                std::string data;
                data.reserve(_rdbuf.size());
                while (!_rdbuf.empty()) {
                    char x = _rdbuf.front();
                    _rdbuf.pop_front();
                    data.push_back(x);
                }
                _doing = false;
                _read_num = -1;
                if (_read_handler) {
                    auto h = _read_handler;
                    _read_handler = ReadHandler();
                    h(data, *this);
                }
                return true;
            }
        }
        // Read until
        else if (_read_until) {
            // SUNDAY FIND
            // Find the _read_until substring
            size_t _until_str_len = strlen(_read_until);
            int char_step[256] = {0};
            for (size_t i = 0; i < 256; ++ i)
                char_step[i] = _until_str_len + 1;
            for (size_t i = 0; i < _until_str_len; ++ i)
                char_step[(size_t) _read_until[i]] = _until_str_len - i;

            auto itr = _rdbuf.begin();
            size_t subind = 0;
            while (itr != _rdbuf.end()) {
                auto tmp = itr;
                while (subind < _until_str_len) {
                    if (*itr == _read_until[subind]) {
                        itr ++;
                        subind ++;
                        continue;
                    }
                    else {
                        if (_rdbuf.end() - tmp < _until_str_len) {
                            // Could not find it.
                            goto SUNDAY_SEARCH_EXIT;
                        }

                        char firstRightChar = *(tmp + _until_str_len);
                        itr = tmp + char_step[(size_t) firstRightChar];
                        subind = 0;
                        break;
                    }
                }

                if (subind == _until_str_len) {
                    // Found it!!
                    std::string data;
                    size_t len = itr - _rdbuf.begin();
                    data.reserve(len);
                    while (len --) {
                        char x = _rdbuf.front();
                        _rdbuf.pop_front();
                        data.push_back(x);
                    }

                    _doing = false;
                    _read_until = nullptr;
                    if (_read_handler) {
                        auto h = _read_handler;
                        _read_handler = ReadHandler();
                        h(data, *this);
                    }
                    return true;
                }
            }
    SUNDAY_SEARCH_EXIT:
            ;
        }

        return false;
    }

HTTP Connection Layer
#####################

The **HTTP Connection Layer** reads data from the ``IOStream`` and exacts the HTTP header and body from it. Also it is responsible for packing the HTTP header and body into a HTTP package and then send it to the ``IOStream``.

With the help of the previous jobs, it is pretty easy to write the ``HttpConnection`` class.

Let's define two helper class: ``HttpRequest`` and ``HttpResponse``.

.. code:: cpp

    struct HttpRequest {
        std::string version = "HTTP/1.1";
        std::string method = "GET";
        std::string uri = "/";
        HeaderMap headers;
        std::string raw_body;
        Remote remote;

        std::map<std::string, std::string> form;
        std::map<std::string, std::string> params;

        class ParseException : public std::invalid_argument {
            public:
                explicit ParseException(const std::string& what_arg);
                explicit ParseException(const char *what_arg);
        };

        void parse_headers(const std::string& raw_header) throw (ParseException);
        void parse_body(const std::string& raw_body) throw (ParseException);

    };

    struct HttpResponse {
        unsigned int status_code = 200;
        std::string response_msg = "OK";
        std::string version = "HTTP/1.1";
        HeaderMap headers;
        std::string body;
        bool close = false;

        std::string make_package();
    };

We can use these two classes to pass and receive data from **Application Layer**. Let's see the ``HttpConnection`` class.

.. code:: cpp

    class HttpConnection {
        public:
            typedef std::function<void (const HttpRequest&, HttpResponse&)> HttpConnectionHandler;

            HttpConnection(const SocketClient& client, IOLoop& loop, const HttpConnectionHandler& handler);
            ~HttpConnection();

            void set_close_callback(const std::function<void (HttpConnection *)>&);
            void close();

        private:
            void __stream_handler_get_header(const std::string&, IOStream&) noexcept;
            void __stream_handler_get_body(const std::string&, IOStream&) noexcept;
            void __stream_handler_on_write(IOStream&) noexcept;

            IOStream _stream;
            HttpConnectionHandler handler;
            HttpRequest request;

            std::function<void (HttpConnection *)> _close_callback;
            bool _closed;
            bool _close_after_finished;
    };

As you can imagine, it is super easy to implement the ``__stream_handler_get_header``, ``__stream_handler_get_body`` and ``__stream_handler_on_write`` with the help of ``IOStream::read_until``, ``IOStream::read_bytes`` and ``IOStream::write_bytes``. Try it yourself ^_^.

Application Layer
#################

This is the last part of our HTTP server. You can design your own application layer in dozens of ways. Here I decide use one of the most simplest way: ``HttpHandler`` class.

.. code:: cpp

    class HttpHandler {
        public:
            HttpHandler();
            virtual ~HttpHandler();

            virtual void prepare(const HttpRequest& request,
                                 HttpResponse& response,
                                 const std::vector<std::string>& urlmatchs);

            virtual void head_handler(const HttpRequest& request,
                                      HttpResponse& response,
                                      const std::vector<std::string>& urlmatchs);
            virtual void get_handler(const HttpRequest& request,
                                     HttpResponse& response,
                                     const std::vector<std::string>& urlmatchs);
            virtual void post_handler(const HttpRequest& request,
                                      HttpResponse& response,
                                      const std::vector<std::string>& urlmatchs);
            virtual void delete_handler(const HttpRequest& request,
                                        HttpResponse& response,
                                        const std::vector<std::string>& urlmatchs);
            virtual void put_handler(const HttpRequest& request,
                                     HttpResponse& response,
                                     const std::vector<std::string>& urlmatchs);
            virtual void options_handler(const HttpRequest& request,
                                         HttpResponse& response,
                                         const std::vector<std::string>& urlmatchs);
            virtual void patch_handler(const HttpRequest& request,
                                       HttpResponse& response,
                                       const std::vector<std::string>& urlmatchs);
            virtual void copy_handler(const HttpRequest& request,
                                      HttpResponse& response,
                                      const std::vector<std::string>& urlmatchs);
            virtual void link_handler(const HttpRequest& request,
                                      HttpResponse& response,
                                      const std::vector<std::string>& urlmatchs);
            virtual void unlink_handler(const HttpRequest& request,
                                        HttpResponse& response,
                                        const std::vector<std::string>& urlmatchs);

            virtual void after(const HttpRequest& request,
                               HttpResponse& response,
                               const std::vector<std::string>& urlmatchs);
    };

It is obvious that if you want to write a handler to process a specific url, just subclass the ``HttpHandler`` and let it bound with a url pattern. When a request comes, the server will call the specific member function of the ``HttpHandler``.

How to match the url pattern? Yes, the **regular expression**. The ``RegExp`` library in C++11 is awesome, but the current version of GCC doesn't support it yet. If you want to use ``RegExp`` in C++11, you have to use clang++ or `Boost Library`_.

.. _`Boost Library`: www.boost.org

Conclusion
==========

Ok, time's up. Today I implemented a very very simple HTTP server. All code could be found in HERE_.

.. _HERE: https://github.com/zonyitoo/HTTPSrv

Happy learning!!
